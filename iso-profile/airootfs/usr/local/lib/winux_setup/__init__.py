"""WINUX First-Boot hardware detection and setup orchestration."""

from .hardware import (
    HardwareSummary,
    detect_hardware,
    is_live_iso,
    resolve_drm_cards_igpu_first,
    write_igpu_kwin_env,
)
from .tasks import build_setup_commands, first_boot_state_path, load_first_boot_state, mark_first_boot_complete

__all__ = [
    "HardwareSummary",
    "build_setup_commands",
    "detect_hardware",
    "first_boot_state_path",
    "is_live_iso",
    "load_first_boot_state",
    "mark_first_boot_complete",
    "resolve_drm_cards_igpu_first",
    "write_igpu_kwin_env",
]
