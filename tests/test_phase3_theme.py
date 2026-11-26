"""Unit and configuration tests for Phase 3 (Windows 10 KDE Plasma 6 theme & UX)."""

from __future__ import annotations

import configparser
import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
AIROOTFS = REPO_ROOT / "iso-profile" / "airootfs"


def _load_script_module(path: Path, name: str):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class Phase3ThemeTests(unittest.TestCase):
    def test_svg_assets_exist_and_are_valid_svg(self) -> None:
        start_svg = AIROOTFS / "usr" / "share" / "icons" / "winux" / "winux-start.svg"
        wall_svg = AIROOTFS / "usr" / "share" / "wallpapers" / "winux" / "winux-hero.svg"
        for svg in (start_svg, wall_svg):
            self.assertTrue(svg.is_file(), f"Missing {svg}")
            text = svg.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("</svg>", text)

    def test_kde_skel_configs_and_shortcuts(self) -> None:
        kdeglobals = configparser.ConfigParser()
        kdeglobals.read(AIROOTFS / "etc" / "skel" / ".config" / "kdeglobals", encoding="utf-8")
        self.assertEqual(kdeglobals.get("KDE", "SingleClick"), "false")
        self.assertEqual(kdeglobals.get("WM", "frame"), "0,120,215")

        shortcuts = configparser.ConfigParser()
        shortcuts.read(AIROOTFS / "etc" / "skel" / ".config" / "kglobalshortcutsrc", encoding="utf-8")
        self.assertIn("Meta+E", shortcuts.get("org.kde.dolphin.desktop][Global Shortcuts", "_launch"))
        self.assertIn(
            "Ctrl+Shift+Esc",
            shortcuts.get("org.kde.plasma-systemmonitor.desktop][Global Shortcuts", "_launch"),
        )
        self.assertIn("Meta+R", shortcuts.get("krunner][Global Shortcuts", "Run Command"))

    def test_plasma_layout_js_contains_win10_elements(self) -> None:
        js_path = AIROOTFS / "usr" / "local" / "share" / "winux" / "plasma-win10-layout.js"
        js = js_path.read_text(encoding="utf-8")
        self.assertIn('taskbar.location = "bottom"', js)
        self.assertIn("taskbar.height = 44", js)
        self.assertIn("org.kde.plasma.kickoff", js)
        self.assertIn("org.kde.plasma.icontasks", js)
        self.assertIn("org.kde.plasma.showdesktop", js)
        self.assertIn("winux-start.svg", js)

    def test_winux_apply_theme_idempotent_and_force(self) -> None:
        mod = _load_script_module(AIROOTFS / "usr" / "local" / "bin" / "winux-apply-theme", "winux_apply_theme")
        layout_js = AIROOTFS / "usr" / "local" / "share" / "winux" / "plasma-win10-layout.js"

        calls: list[list[str]] = []

        def fake_run(cmd: list[str], check: bool = False):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "winux" / "theme-applied"
            rc1 = mod.apply_layout(
                layout_js=layout_js,
                marker=marker,
                which_fn=lambda name: "/usr/bin/qdbus6" if name == "qdbus6" else None,
                run_fn=fake_run,
            )
            self.assertEqual(rc1, 0)
            self.assertTrue(marker.is_file())
            self.assertEqual(len(calls), 1)

            # Second call without --force must be a no-op
            rc2 = mod.apply_layout(
                layout_js=layout_js,
                marker=marker,
                which_fn=lambda name: "/usr/bin/qdbus6" if name == "qdbus6" else None,
                run_fn=fake_run,
            )
            self.assertEqual(rc2, 0)
            self.assertEqual(len(calls), 1)

            # --force re-applies
            rc3 = mod.apply_layout(
                layout_js=layout_js,
                marker=marker,
                force=True,
                which_fn=lambda name: "/usr/bin/qdbus6" if name == "qdbus6" else None,
                run_fn=fake_run,
            )
            self.assertEqual(rc3, 0)
            self.assertEqual(len(calls), 2)

    def test_systemd_preset_enables_core_services(self) -> None:
        preset = (AIROOTFS / "etc" / "systemd" / "system-preset" / "10-winux.preset").read_text(encoding="utf-8")
        for svc in ("enable sddm.service", "enable NetworkManager.service", "enable systemd-binfmt.service"):
            self.assertIn(svc, preset)


if __name__ == "__main__":
    unittest.main()
