"""Unit tests for the WINUX Phase 2 Windows compatibility package."""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent.parent / "iso-profile" / "airootfs" / "usr" / "local" / "lib"
sys.path.insert(0, str(LIB_DIR))

from winux_compat.config import PrefixConfig, sanitize_prefix_name  # noqa: E402
from winux_compat.detector import classify_target, detect_anticheat, inspect_pe  # noqa: E402
from winux_compat.prefixes import PrefixManager  # noqa: E402
from winux_compat.runner import build_command, build_environment  # noqa: E402
from winux_compat.shortcuts import generate_shortcuts_for_prefix, scan_prefix_executables  # noqa: E402


def _make_minimal_pe(path: Path, *, machine: int = 0x8664, subsystem: int = 2) -> None:
    """Write a minimal valid DOS + PE/COFF + Optional header for testing."""
    dos = bytearray(64)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 64)

    coff = bytearray(24)
    coff[0:4] = b"PE\x00\x00"
    struct.pack_into("<HHIIIHH", coff, 4, machine, 0, 0, 0, 0, 72, 0)

    opt = bytearray(72)
    struct.pack_into("<H", opt, 68, subsystem)

    path.write_bytes(bytes(dos + coff + opt))


class WinuxCompatTests(unittest.TestCase):
    def test_sanitize_prefix_name_prevents_traversal(self) -> None:
        self.assertEqual(sanitize_prefix_name("../../etc/passwd"), "etc-passwd")
        self.assertEqual(sanitize_prefix_name(".."), "default")
        self.assertEqual(sanitize_prefix_name("Cyber Game 2077"), "Cyber-Game-2077")

    def test_pe_inspection_and_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_exe = root / "NotepadClone.exe"
            _make_minimal_pe(app_exe, machine=0x8664, subsystem=2)
            info = inspect_pe(app_exe)
            self.assertTrue(info.is_pe)
            self.assertEqual(info.arch, "x64")
            self.assertEqual(info.subsystem, "gui")
            self.assertEqual(info.classification, "app")

            setup_exe = root / "MyAppSetup.exe"
            _make_minimal_pe(setup_exe, machine=0x014C, subsystem=2)
            setup_info = inspect_pe(setup_exe)
            self.assertEqual(setup_info.arch, "x86")
            self.assertEqual(setup_info.classification, "installer")

            game_dir = root / "Games" / "CoolRPG"
            game_dir.mkdir(parents=True)
            game_exe = game_dir / "CoolRPG.exe"
            _make_minimal_pe(game_exe)
            (game_dir / "d3d11.dll").write_bytes(b"")
            self.assertEqual(classify_target(game_exe), "game")

            msi = root / "installer.msi"
            msi.write_bytes(b"")
            self.assertEqual(inspect_pe(msi).classification, "installer")

    def test_prefix_lifecycle_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = PrefixManager(root=Path(tmp))
            prefix_dir, cfg = manager.ensure_prefix("My Game", mode="game")
            self.assertTrue((prefix_dir / "winux-prefix.json").is_file())
            self.assertEqual(cfg.mode, "game")
            self.assertTrue(cfg.gamescope)

            reloaded = PrefixConfig.load(prefix_dir)
            self.assertEqual(reloaded.name, "My-Game")
            self.assertEqual(len(manager.list_prefixes()), 1)
            self.assertTrue(manager.remove_prefix("My Game"))
            self.assertEqual(len(manager.list_prefixes()), 0)

    def test_runner_command_and_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_ntsync = root / "ntsync"
            fake_ntsync.write_text("", encoding="utf-8")
            prefix_dir = root / "prefix"
            prefix_dir.mkdir()

            cfg = PrefixConfig(name="game1", mode="game", runner="auto", gamemode=True, gamescope=True, mangohud=True)
            env = build_environment(prefix_dir, cfg, ntsync_device=fake_ntsync)
            self.assertEqual(env["WINEPREFIX"], str(prefix_dir))
            self.assertEqual(env["PROTON_USE_NTSYNC"], "1")
            self.assertEqual(env["MANGOHUD"], "1")

            env_fallback = build_environment(prefix_dir, cfg, ntsync_device=root / "missing")
            self.assertEqual(env_fallback["WINEFSYNC"], "1")

            fake_tools = {
                "umu-run": "/usr/bin/umu-run",
                "wine": "/usr/bin/wine",
                "gamemoderun": "/usr/bin/gamemoderun",
                "gamescope": "/usr/bin/gamescope",
            }
            cmd = build_command(root / "game.exe", ["--dx12"], cfg, which_fn=fake_tools.get)
            self.assertEqual(
                cmd,
                [
                    "/usr/bin/gamescope",
                    "-f",
                    "--",
                    "/usr/bin/gamemoderun",
                    "/usr/bin/umu-run",
                    str(root / "game.exe"),
                    "--dx12",
                ],
            )

            msi_cmd = build_command(root / "app.msi", [], cfg, which_fn=fake_tools.get)
            self.assertEqual(msi_cmd, ["/usr/bin/wine", "msiexec", "/i", str(root / "app.msi")])

    def test_shortcut_scanning_and_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prefix_dir = root / "prefixes" / "office"
            prog_dir = prefix_dir / "drive_c" / "Program Files" / "NoteApp"
            prog_dir.mkdir(parents=True)

            app_exe = prog_dir / "NoteApp.exe"
            uninst_exe = prog_dir / "unins000.exe"
            _make_minimal_pe(app_exe)
            _make_minimal_pe(uninst_exe)

            discovered = scan_prefix_executables(prefix_dir)
            self.assertEqual(discovered, [app_exe])

            cfg = PrefixConfig(name="office", mode="app")
            apps_dir = root / "applications"
            icons_dir = root / "icons"
            created = generate_shortcuts_for_prefix(prefix_dir, cfg, apps_dir=apps_dir, icons_dir=icons_dir)
            self.assertEqual(len(created), 1)
            desktop_text = created[0].read_text(encoding="utf-8")
            self.assertIn("Name=NoteApp", desktop_text)
            self.assertIn('Exec=/usr/local/bin/winux-exec --prefix "office"', desktop_text)
            self.assertIn("Categories=Utility;", desktop_text)

    def test_detect_anticheat_distinguishes_kernel_blockers_and_optin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean_app"
            clean_dir.mkdir()
            clean_exe = clean_dir / "App.exe"
            _make_minimal_pe(clean_exe)
            self.assertIsNone(detect_anticheat(clean_exe))

            val_dir = root / "shooter"
            val_dir.mkdir()
            val_exe = val_dir / "Game.exe"
            _make_minimal_pe(val_exe)
            (val_dir / "vgk.sys").write_bytes(b"")
            finding = detect_anticheat(val_exe)
            self.assertIsNotNone(finding)
            assert finding is not None
            self.assertTrue(finding.blocking)
            self.assertEqual(finding.name, "Riot Vanguard")

            eac_dir = root / "coop" / "EasyAntiCheat"
            eac_dir.mkdir(parents=True)
            coop_exe = root / "coop" / "Coop.exe"
            _make_minimal_pe(coop_exe)
            (eac_dir / "EasyAntiCheat.sys").write_bytes(b"")
            eac_finding = detect_anticheat(coop_exe)
            self.assertIsNotNone(eac_finding)
            assert eac_finding is not None
            self.assertFalse(eac_finding.blocking)
            self.assertEqual(eac_finding.name, "Easy Anti-Cheat")


if __name__ == "__main__":
    unittest.main()
