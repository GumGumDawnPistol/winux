"""PE binary inspection and heuristic game/app/installer classification."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

BinaryKind = Literal["game", "app", "installer", "unknown"]

_IMAGE_FILE_MACHINE_I386 = 0x014C
_IMAGE_FILE_MACHINE_AMD64 = 0x8664
_IMAGE_FILE_MACHINE_ARM64 = 0xAA64

_SUBSYSTEM_WINDOWS_GUI = 2
_SUBSYSTEM_WINDOWS_CUI = 3

_INSTALLER_HINTS = ("setup", "install", "installer", "redist", "vcredist", "dxsetup")
_GAME_DIR_HINTS = ("steamapps", "epic games", "gog games", "games", "riot games", "ubisoft", "ea games")
_GAME_DLL_HINTS = (
    "d3d9.dll",
    "d3d11.dll",
    "d3d12.dll",
    "dxgi.dll",
    "xinput1_3.dll",
    "xinput1_4.dll",
    "unityplayer.dll",
    "steam_api64.dll",
    "steam_api.dll",
    "eoossdk-win64-shipping.dll",
)

_KERNEL_BLOCKER_ANTICHEATS: dict[str, str] = {
    "vgk.sys": "Riot Vanguard",
    "randgrid.sys": "Call of Duty Ricochet",
    "mhyprot2.sys": "miHoYo Protect",
    "mhyprot3.sys": "miHoYo Protect",
    "ace-base.sys": "Anti-Cheat Expert",
}

_PROTON_OPTIN_ANTICHEATS: dict[str, str] = {
    "bedaisy.sys": "BattlEye",
    "easyanticheat.sys": "Easy Anti-Cheat",
    "easyanticheat_eos.sys": "Easy Anti-Cheat (EOS)",
}


@dataclass(frozen=True)
class AnticheatFinding:
    """Detected anti-cheat driver/marker alongside Linux compatibility level."""

    name: str
    marker: str
    blocking: bool


@dataclass(frozen=True)
class BinaryInfo:
    """Metadata extracted from a Windows PE executable or MSI installer."""

    path: Path
    is_pe: bool
    is_msi: bool
    arch: str
    subsystem: str
    classification: BinaryKind


def inspect_pe(target: Path) -> BinaryInfo:
    """Parse minimal DOS/COFF/Optional PE headers without external dependencies."""
    suffix = target.suffix.lower()
    if suffix == ".msi":
        return BinaryInfo(
            path=target,
            is_pe=False,
            is_msi=True,
            arch="msi",
            subsystem="installer",
            classification="installer",
        )

    is_pe = False
    arch = "unknown"
    subsystem = "unknown"

    try:
        with target.open("rb") as fh:
            dos_header = fh.read(64)
            if len(dos_header) == 64 and dos_header[:2] == b"MZ":
                pe_offset = struct.unpack_from("<I", dos_header, 0x3C)[0]
                fh.seek(pe_offset)
                pe_sig_and_coff = fh.read(24)
                if len(pe_sig_and_coff) == 24 and pe_sig_and_coff[:4] == b"PE\x00\x00":
                    is_pe = True
                    machine, _, _, _, _, opt_size, _ = struct.unpack_from("<HHIIIHH", pe_sig_and_coff, 4)
                    arch = {
                        _IMAGE_FILE_MACHINE_I386: "x86",
                        _IMAGE_FILE_MACHINE_AMD64: "x64",
                        _IMAGE_FILE_MACHINE_ARM64: "arm64",
                    }.get(machine, f"0x{machine:04x}")

                    if opt_size >= 70:
                        opt_header = fh.read(70)
                        if len(opt_header) >= 70:
                            sub_val = struct.unpack_from("<H", opt_header, 68)[0]
                            subsystem = {
                                _SUBSYSTEM_WINDOWS_GUI: "gui",
                                _SUBSYSTEM_WINDOWS_CUI: "console",
                            }.get(sub_val, f"subsystem-{sub_val}")
    except OSError:
        pass

    classification = classify_target(target, is_pe=is_pe, is_msi=False)
    return BinaryInfo(
        path=target,
        is_pe=is_pe,
        is_msi=False,
        arch=arch,
        subsystem=subsystem,
        classification=classification,
    )


def classify_target(target: Path, *, is_pe: bool = True, is_msi: bool = False) -> BinaryKind:
    """Heuristically classify a Windows binary as installer, game, or desktop app."""
    if is_msi or target.suffix.lower() == ".msi":
        return "installer"
    if not is_pe and target.suffix.lower() != ".exe":
        return "unknown"

    lower_name = target.name.lower()
    if any(hint in lower_name for hint in _INSTALLER_HINTS):
        return "installer"

    lower_path = str(target).lower()
    if any(hint in lower_path for hint in _GAME_DIR_HINTS):
        return "game"

    parent = target.parent
    if parent.is_dir():
        try:
            sibling_names = {entry.name.lower() for entry in parent.iterdir()}
        except OSError:
            sibling_names = set()
        if any(dll in sibling_names for dll in _GAME_DLL_HINTS):
            return "game"

    return "app"


def detect_anticheat(target: Path) -> AnticheatFinding | None:
    """Inspect target directory (bounded 2-level scan) for Windows anti-cheat drivers."""
    root = target.parent
    if not root.is_dir():
        return None

    candidates: list[Path] = []
    try:
        for entry in root.iterdir():
            candidates.append(entry)
            if entry.is_dir():
                try:
                    candidates.extend(entry.iterdir())
                except OSError:
                    continue
    except OSError:
        return None

    for item in candidates:
        lower = item.name.lower()
        if lower in _KERNEL_BLOCKER_ANTICHEATS:
            return AnticheatFinding(
                name=_KERNEL_BLOCKER_ANTICHEATS[lower],
                marker=item.name,
                blocking=True,
            )
        if lower in _PROTON_OPTIN_ANTICHEATS:
            return AnticheatFinding(
                name=_PROTON_OPTIN_ANTICHEATS[lower],
                marker=item.name,
                blocking=False,
            )
    return None
