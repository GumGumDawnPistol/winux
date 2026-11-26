"""Configuration, XDG paths, and per-prefix metadata persistence."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

PrefixMode = Literal["app", "game"]
RunnerKind = Literal["auto", "umu", "wine"]

COMMON_RUNTIMES: dict[str, str] = {
    "vcrun2022": "Visual C++ 2015-2022 Redistributable",
    "corefonts": "Microsoft Core Fonts",
    "dotnet48": ".NET Framework 4.8",
    "dotnetdesktop6": ".NET 6 Desktop Runtime",
    "dxvk": "DirectX 9/10/11 to Vulkan (DXVK)",
}

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def default_prefix_root() -> Path:
    """Return the XDG data directory used to store WINUX Wine prefixes."""
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return xdg_data / "winux" / "prefixes"


def default_applications_dir() -> Path:
    """Return the XDG applications directory for generated .desktop shortcuts."""
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return xdg_data / "applications"


def default_icons_dir() -> Path:
    """Return the XDG icons directory for extracted Windows app icons."""
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return xdg_data / "icons" / "winux"


def default_state_dir() -> Path:
    """Return the XDG state directory for WINUX runtime logs."""
    xdg_state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return xdg_state / "winux"


def sanitize_prefix_name(raw_name: str) -> str:
    """Normalize a prefix name into a safe single directory component."""
    cleaned = _SAFE_NAME_RE.sub("-", raw_name.strip()).strip(".-")
    if not cleaned or cleaned in {".", ".."}:
        return "default"
    return cleaned[:64]


@dataclass
class PrefixConfig:
    """Persistent configuration stored in each prefix's winux-prefix.json."""

    name: str
    mode: PrefixMode = "app"
    runner: RunnerKind = "auto"
    gamemode: bool = True
    gamescope: bool = False
    mangohud: bool = False
    ntsync: bool = True
    installed_deps: list[str] = field(default_factory=list)
    env_overrides: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, prefix_dir: Path, default_name: str | None = None) -> PrefixConfig:
        """Load winux-prefix.json from prefix_dir or return defaults."""
        cfg_path = prefix_dir / "winux-prefix.json"
        name = sanitize_prefix_name(default_name or prefix_dir.name)
        if not cfg_path.is_file():
            return cls(name=name)

        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        return cls(
            name=sanitize_prefix_name(data.get("name", name)),
            mode="game" if data.get("mode") == "game" else "app",
            runner=data.get("runner", "auto") if data.get("runner") in {"auto", "umu", "wine"} else "auto",
            gamemode=bool(data.get("gamemode", True)),
            gamescope=bool(data.get("gamescope", False)),
            mangohud=bool(data.get("mangohud", False)),
            ntsync=bool(data.get("ntsync", True)),
            installed_deps=list(data.get("installed_deps", [])),
            env_overrides={str(k): str(v) for k, v in dict(data.get("env_overrides", {})).items()},
        )

    def save(self, prefix_dir: Path) -> Path:
        """Persist winux-prefix.json into prefix_dir."""
        prefix_dir.mkdir(parents=True, exist_ok=True)
        cfg_path = prefix_dir / "winux-prefix.json"
        cfg_path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        return cfg_path
