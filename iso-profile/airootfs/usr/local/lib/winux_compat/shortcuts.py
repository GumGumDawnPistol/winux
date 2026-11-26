"""XDG .desktop shortcut generation and icon extraction for installed Windows apps."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import (
    PrefixConfig,
    default_applications_dir,
    default_icons_dir,
    sanitize_prefix_name,
)

_SKIP_EXE_PATTERNS = (
    "unins",
    "uninstall",
    "setup",
    "update",
    "updater",
    "crash",
    "report",
    "helper",
    "redist",
    "dxsetup",
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "app"


def scan_prefix_executables(prefix_dir: Path) -> list[Path]:
    """Discover likely user-facing Windows executables inside a Wine prefix."""
    drive_c = prefix_dir / "drive_c"
    if not drive_c.is_dir():
        return []

    search_roots = [
        drive_c / "Program Files",
        drive_c / "Program Files (x86)",
    ]
    users_dir = drive_c / "users"
    if users_dir.is_dir():
        for user_home in users_dir.iterdir():
            local_programs = user_home / "AppData" / "Local" / "Programs"
            if local_programs.is_dir():
                search_roots.append(local_programs)

    found: list[Path] = []
    for root in search_roots:
        if not root.is_dir():
            continue
        for exe in root.rglob("*.exe"):
            lower_name = exe.name.lower()
            if any(pat in lower_name for pat in _SKIP_EXE_PATTERNS):
                continue
            found.append(exe)
    return sorted(found)


def extract_icon(exe_path: Path, output_name: str, icons_dir: Path | None = None) -> str:
    """Extract an icon via icoutils (wrestool/icotool) or fall back to a generic icon name."""
    wrestool = shutil.which("wrestool")
    icotool = shutil.which("icotool")
    if not wrestool or not icotool:
        return "application-x-ms-dos-executable"

    target_dir = icons_dir or default_icons_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    png_path = target_dir / f"{output_name}.png"

    with tempfile.TemporaryDirectory() as tmp:
        ico_path = Path(tmp) / "app.ico"
        res = subprocess.run(
            [wrestool, "-x", "-t", "14", str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if res.returncode != 0 or not res.stdout:
            return "application-x-ms-dos-executable"
        ico_path.write_bytes(res.stdout)

        conv = subprocess.run(
            [icotool, "-x", "-o", tmp, str(ico_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if conv.returncode != 0:
            return "application-x-ms-dos-executable"

        pngs = sorted(Path(tmp).glob("*.png"), key=lambda p: p.stat().st_size, reverse=True)
        if not pngs:
            return "application-x-ms-dos-executable"
        shutil.copy2(pngs[0], png_path)
        return str(png_path)


def write_desktop_shortcut(
    exe_path: Path,
    cfg: PrefixConfig,
    *,
    apps_dir: Path | None = None,
    icons_dir: Path | None = None,
) -> Path:
    """Create a Start Menu .desktop entry launching exe_path through winux-exec."""
    out_dir = apps_dir or default_applications_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix_slug = sanitize_prefix_name(cfg.name)
    app_slug = _slugify(exe_path.stem)
    desktop_id = f"winux-{prefix_slug}-{app_slug}"
    desktop_path = out_dir / f"{desktop_id}.desktop"

    icon = extract_icon(exe_path, desktop_id, icons_dir=icons_dir)
    game_flag = " --game" if cfg.mode == "game" else ""
    category = "Game;" if cfg.mode == "game" else "Utility;"

    content = (
        "[Desktop Entry]\n"
        f"Name={exe_path.stem}\n"
        f"Comment=Windows {cfg.mode} via WINUX ({cfg.name})\n"
        f'Exec=/usr/local/bin/winux-exec --prefix "{cfg.name}"{game_flag} "{exe_path}"\n'
        f"Icon={icon}\n"
        "Terminal=false\n"
        "Type=Application\n"
        f"Categories={category}\n"
    )
    desktop_path.write_text(content, encoding="utf-8")
    return desktop_path


def generate_shortcuts_for_prefix(
    prefix_dir: Path,
    cfg: PrefixConfig,
    *,
    apps_dir: Path | None = None,
    icons_dir: Path | None = None,
) -> list[Path]:
    """Scan a prefix and generate .desktop shortcuts for discovered executables."""
    created: list[Path] = []
    for exe in scan_prefix_executables(prefix_dir):
        created.append(write_desktop_shortcut(exe, cfg, apps_dir=apps_dir, icons_dir=icons_dir))
    return created
