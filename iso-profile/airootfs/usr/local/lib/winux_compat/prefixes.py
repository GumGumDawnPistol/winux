"""Wine prefix lifecycle and Windows dependency bootstrapping."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .config import PrefixConfig, PrefixMode, default_prefix_root, sanitize_prefix_name


class PrefixManager:
    """Manage isolated WINUX Wine/Proton prefixes under a root directory."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_prefix_root()).resolve()

    def prefix_path(self, name: str) -> Path:
        """Resolve a sanitized prefix directory safely inside self.root."""
        safe = sanitize_prefix_name(name)
        candidate = (self.root / safe).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"Unsafe prefix path: {name}")
        return candidate

    def ensure_prefix(self, name: str, mode: PrefixMode | None = None) -> tuple[Path, PrefixConfig]:
        """Create a prefix directory and metadata file if missing."""
        safe = sanitize_prefix_name(name)
        prefix_dir = self.prefix_path(safe)
        existed = (prefix_dir / "winux-prefix.json").is_file()
        is_new_dir = not prefix_dir.exists()
        prefix_dir.mkdir(parents=True, exist_ok=True)
        if is_new_dir:
            self._apply_nodatacow(prefix_dir)
        cfg = PrefixConfig.load(prefix_dir, default_name=safe)
        if not existed and mode is not None:
            cfg.mode = mode
            cfg.gamescope = mode == "game"
        cfg.save(prefix_dir)
        return prefix_dir, cfg

    @staticmethod
    def _apply_nodatacow(prefix_dir: Path) -> None:
        """Best-effort chattr +C on empty prefix dirs to avoid Btrfs CoW bloat."""
        chattr = shutil.which("chattr")
        if not chattr:
            return
        try:
            subprocess.run(
                [chattr, "+C", str(prefix_dir)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            pass

    def list_prefixes(self) -> list[tuple[Path, PrefixConfig]]:
        """Return all prefixes currently stored under self.root."""
        if not self.root.is_dir():
            return []
        results: list[tuple[Path, PrefixConfig]] = []
        for entry in sorted(self.root.iterdir()):
            if entry.is_dir():
                results.append((entry, PrefixConfig.load(entry, default_name=entry.name)))
        return results

    def remove_prefix(self, name: str) -> bool:
        """Delete a prefix directory if it exists."""
        prefix_dir = self.prefix_path(name)
        if not prefix_dir.exists():
            return False
        shutil.rmtree(prefix_dir)
        return True

    def install_dependencies(self, name: str, verbs: list[str], *, force: bool = False) -> list[str]:
        """Install requested winetricks verbs into a prefix, skipping already installed ones."""
        prefix_dir, cfg = self.ensure_prefix(name)
        pending = [v for v in verbs if force or v not in cfg.installed_deps]
        if not pending:
            return []

        winetricks = shutil.which("winetricks")
        if not winetricks:
            raise FileNotFoundError("winetricks is not installed")

        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix_dir)
        env.setdefault("WINEARCH", "win64")

        subprocess.run([winetricks, "-q", *pending], env=env, check=True)
        for verb in pending:
            if verb not in cfg.installed_deps:
                cfg.installed_deps.append(verb)
        cfg.save(prefix_dir)
        return pending
