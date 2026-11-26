"""First-boot setup task builders and completion-state persistence."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .hardware import HardwareSummary


@dataclass(frozen=True)
class SetupTask:
    """Declarative setup command presented in the WINUX First-Boot Wizard."""

    task_id: str
    title: str
    command: list[str]
    requires_root: bool = False


def first_boot_state_path() -> Path:
    """Return the XDG config path storing first-boot completion metadata."""
    xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return xdg_config / "winux" / "first-boot.json"


def load_first_boot_state(state_path: Path | None = None) -> dict[str, object]:
    """Load first-boot completion state or return an uncompleted default dict."""
    target = state_path or first_boot_state_path()
    if not target.is_file():
        return {"completed": False, "tasks": []}
    return json.loads(target.read_text(encoding="utf-8"))


def mark_first_boot_complete(completed_tasks: list[str], state_path: Path | None = None) -> Path:
    """Persist first-boot completion status so the wizard does not auto-launch again."""
    target = state_path or first_boot_state_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"completed": True, "tasks": list(completed_tasks)}
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def build_setup_commands(
    hw: HardwareSummary,
    *,
    enable_flathub: bool = True,
    install_gaming_apps: bool = True,
    bootstrap_win_runtimes: bool = True,
    install_nvidia: bool | None = None,
) -> list[SetupTask]:
    """Generate ordered post-install setup commands tailored to detected hardware."""
    tasks: list[SetupTask] = []

    want_nvidia = ("nvidia" in hw.gpu_vendors) if install_nvidia is None else install_nvidia
    if want_nvidia:
        tasks.append(
            SetupTask(
                task_id="nvidia-drivers",
                title="Install proprietary NVIDIA driver & 32-bit Vulkan libraries",
                command=[
                    "pkexec",
                    "pacman",
                    "-S",
                    "--noconfirm",
                    "--needed",
                    "nvidia-dkms",
                    "nvidia-utils",
                    "lib32-nvidia-utils",
                ],
                requires_root=True,
            )
        )

    if enable_flathub:
        tasks.append(
            SetupTask(
                task_id="flathub",
                title="Enable Flathub repository for Linux desktop & gaming apps",
                command=[
                    "flatpak",
                    "remote-add",
                    "--if-not-exists",
                    "--user",
                    "flathub",
                    "https://dl.flathub.org/repo/flathub.flatpakrepo",
                ],
            )
        )

    if install_gaming_apps:
        tasks.append(
            SetupTask(
                task_id="gaming-flatpaks",
                title="Install Heroic Games Launcher & ProtonUp-Qt (Flatpak)",
                command=[
                    "flatpak",
                    "install",
                    "-y",
                    "--user",
                    "flathub",
                    "com.heroicgameslauncher.hgl",
                    "net.davidotek.pupgui2",
                ],
            )
        )

    if bootstrap_win_runtimes:
        tasks.append(
            SetupTask(
                task_id="winux-runtimes",
                title="Initialize default Windows prefix (vcrun2022 + corefonts)",
                command=[
                    "/usr/local/bin/winux-exec",
                    "--prefix",
                    "default",
                    "--deps",
                    "vcrun2022",
                    "corefonts",
                ],
            )
        )

    return tasks
