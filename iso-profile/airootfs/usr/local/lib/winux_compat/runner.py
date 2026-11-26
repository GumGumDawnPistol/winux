"""Command construction, environment setup, and execution logging."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .config import PrefixConfig, default_state_dir
from .detector import inspect_pe


def has_ntsync(dev_path: Path = Path("/dev/ntsync")) -> bool:
    """Return True if the Linux kernel ntsync device node is available."""
    return dev_path.exists()


def build_environment(
    prefix_dir: Path,
    cfg: PrefixConfig,
    *,
    ntsync_device: Path = Path("/dev/ntsync"),
) -> dict[str, str]:
    """Build Wine/Proton environment variables based on prefix config and host kernel."""
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix_dir)
    env.setdefault("WINEARCH", "win64")

    if cfg.ntsync and has_ntsync(ntsync_device):
        env.setdefault("PROTON_USE_NTSYNC", "1")
    else:
        env.setdefault("WINEFSYNC", "1")

    if cfg.mangohud:
        env["MANGOHUD"] = "1"

    env.update(cfg.env_overrides)
    return env


def build_command(
    target: Path,
    target_args: list[str],
    cfg: PrefixConfig,
    *,
    which_fn=shutil.which,
) -> list[str]:
    """Build the runner invocation for a Windows .exe or .msi binary."""
    if target.suffix.lower() == ".msi":
        wine = which_fn("wine")
        if not wine:
            raise FileNotFoundError("wine is not installed")
        return [wine, "msiexec", "/i", str(target), *target_args]

    umu_run = which_fn("umu-run")
    prefer_umu = cfg.runner == "umu" or (cfg.runner == "auto" and cfg.mode == "game")

    if prefer_umu and umu_run:
        cmd = [umu_run, str(target), *target_args]
    else:
        if cfg.runner == "umu" and not umu_run:
            raise FileNotFoundError("umu-run is not installed")
        wine = which_fn("wine")
        if not wine:
            raise FileNotFoundError("wine is not installed")
        cmd = [wine, str(target), *target_args]

    if cfg.mode == "game":
        if cfg.gamemode:
            gamemoderun = which_fn("gamemoderun")
            if gamemoderun:
                cmd = [gamemoderun, *cmd]
        if cfg.gamescope:
            gamescope = which_fn("gamescope")
            if gamescope:
                cmd = [gamescope, "-f", "--", *cmd]

    return cmd


def log_launch(target: Path, cfg: PrefixConfig, cmd: list[str], state_dir: Path | None = None) -> None:
    """Append a structured launch line to WINUX runtime logs (best effort)."""
    try:
        log_root = state_dir or default_state_dir()
        log_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat()
        line = f"{stamp} prefix={cfg.name} mode={cfg.mode} target={target} cmd={' '.join(cmd)}\n"
        with (log_root / "winux-exec.log").open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass


def launch_target(
    target: Path,
    target_args: list[str],
    prefix_dir: Path,
    cfg: PrefixConfig,
) -> int:
    """Inspect, configure, log, and execute a Windows binary."""
    inspect_pe(target)
    env = build_environment(prefix_dir, cfg)
    cmd = build_command(target, target_args, cfg)
    log_launch(target, cfg, cmd)
    return subprocess.call(cmd, env=env)
