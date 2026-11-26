"""Hardware and kernel capability detection for WINUX first-boot setup."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

_PCI_VENDOR_MAP = {
    "0x10de": "nvidia",
    "0x1002": "amd",
    "0x8086": "intel",
}
_CARD_NAME_RE = re.compile(r"^card\d+$")


@dataclass(frozen=True)
class HardwareSummary:
    """Detected GPU vendors, kernel ntsync support, and live-ISO status."""

    gpu_vendors: tuple[str, ...]
    ntsync_available: bool
    is_live_session: bool


def is_live_iso(archiso_run_dir: Path = Path("/run/archiso")) -> bool:
    """Return True when running inside the archiso Live environment."""
    return archiso_run_dir.exists()


def detect_gpu_vendors(drm_root: Path = Path("/sys/class/drm")) -> tuple[str, ...]:
    """Inspect sysfs DRM vendor IDs and return deduplicated GPU vendor names."""
    if not drm_root.is_dir():
        return ()

    vendors: list[str] = []
    for card in sorted(drm_root.iterdir()):
        if not _CARD_NAME_RE.match(card.name):
            continue
        vendor_file = card / "device" / "vendor"
        if not vendor_file.is_file():
            continue
        try:
            raw = vendor_file.read_text(encoding="utf-8").strip().lower()
        except OSError:
            continue
        mapped = _PCI_VENDOR_MAP.get(raw, raw)
        if mapped not in vendors:
            vendors.append(mapped)
    return tuple(vendors)


def resolve_drm_cards_igpu_first(drm_root: Path = Path("/sys/class/drm")) -> list[str]:
    """Return /dev/dri/cardN paths ordered with integrated GPUs before NVIDIA dGPUs."""
    if not drm_root.is_dir():
        return []

    igpus: list[str] = []
    dgpus: list[str] = []
    for card in sorted(drm_root.iterdir()):
        if not _CARD_NAME_RE.match(card.name):
            continue
        vendor_file = card / "device" / "vendor"
        if not vendor_file.is_file():
            continue
        try:
            raw = vendor_file.read_text(encoding="utf-8").strip().lower()
        except OSError:
            continue
        dev_node = f"/dev/dri/{card.name}"
        if raw in {"0x8086", "0x1002"}:
            igpus.append(dev_node)
        else:
            dgpus.append(dev_node)
    return igpus + dgpus


def write_igpu_kwin_env(
    *,
    env_dir: Path | None = None,
    drm_root: Path = Path("/sys/class/drm"),
) -> Path | None:
    """Write Plasma KWIN_DRM_DEVICES env script prioritizing iGPU over NVIDIA dGPU."""
    cards = resolve_drm_cards_igpu_first(drm_root=drm_root)
    if len(cards) < 2:
        return None

    target_dir = env_dir or (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "plasma-workspace"
        / "env"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / "winux-gpu.sh"
    out_file.write_text(f"export KWIN_DRM_DEVICES={':'.join(cards)}\n", encoding="utf-8")
    return out_file


def detect_hardware(
    *,
    drm_root: Path = Path("/sys/class/drm"),
    ntsync_dev: Path = Path("/dev/ntsync"),
    archiso_run_dir: Path = Path("/run/archiso"),
) -> HardwareSummary:
    """Collect a summary of GPU vendors, ntsync availability, and Live ISO status."""
    return HardwareSummary(
        gpu_vendors=detect_gpu_vendors(drm_root=drm_root),
        ntsync_available=ntsync_dev.exists(),
        is_live_session=is_live_iso(archiso_run_dir=archiso_run_dir),
    )
