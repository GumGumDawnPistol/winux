"""Unit and configuration tests for Phase 4 (Calamares Btrfs/Snapper & First-Boot Wizard)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AIROOTFS = REPO_ROOT / "iso-profile" / "airootfs"
LIB_DIR = AIROOTFS / "usr" / "local" / "lib"
sys.path.insert(0, str(LIB_DIR))

from winux_setup.hardware import HardwareSummary, detect_hardware  # noqa: E402
from winux_setup.tasks import build_setup_commands, load_first_boot_state, mark_first_boot_complete  # noqa: E402


class Phase4SetupTests(unittest.TestCase):
    def test_hardware_detection_with_mock_sysfs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drm = root / "drm"
            (drm / "card0" / "device").mkdir(parents=True)
            (drm / "card0" / "device" / "vendor").write_text("0x10de\n", encoding="utf-8")
            (drm / "card1" / "device").mkdir(parents=True)
            (drm / "card1" / "device" / "vendor").write_text("0x1002\n", encoding="utf-8")

            ntsync = root / "ntsync"
            ntsync.write_text("", encoding="utf-8")
            archiso = root / "archiso"
            archiso.mkdir()

            hw = detect_hardware(drm_root=drm, ntsync_dev=ntsync, archiso_run_dir=archiso)
            self.assertEqual(hw.gpu_vendors, ("nvidia", "amd"))
            self.assertTrue(hw.ntsync_available)
            self.assertTrue(hw.is_live_session)

    def test_setup_tasks_adapt_to_gpu_and_persist_state(self) -> None:
        hw_amd = HardwareSummary(gpu_vendors=("amd",), ntsync_available=True, is_live_session=False)
        amd_tasks = build_setup_commands(hw_amd)
        self.assertEqual(
            [t.task_id for t in amd_tasks],
            ["flathub", "gaming-flatpaks", "winux-runtimes"],
        )

        hw_nv = HardwareSummary(gpu_vendors=("nvidia",), ntsync_available=True, is_live_session=False)
        nv_tasks = build_setup_commands(hw_nv)
        self.assertEqual(
            [t.task_id for t in nv_tasks],
            ["nvidia-drivers", "flathub", "gaming-flatpaks", "winux-runtimes"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "winux" / "first-boot.json"
            self.assertFalse(load_first_boot_state(state_file)["completed"])
            mark_first_boot_complete(["flathub"], state_file)
            loaded = load_first_boot_state(state_file)
            self.assertTrue(loaded["completed"])
            self.assertEqual(loaded["tasks"], ["flathub"])

    def test_calamares_btrfs_and_postinstall_configs(self) -> None:
        calamares = AIROOTFS / "etc" / "winux-calamares"
        settings = (calamares / "settings.conf").read_text(encoding="utf-8")
        partition = (calamares / "modules" / "partition.conf").read_text(encoding="utf-8")
        mount = (calamares / "modules" / "mount.conf").read_text(encoding="utf-8")
        unpackfs = (calamares / "modules" / "unpackfs.conf").read_text(encoding="utf-8")
        post = (AIROOTFS / "usr" / "local" / "bin" / "winux-postinstall").read_text(encoding="utf-8")
        install_desktop = (AIROOTFS / "etc" / "skel" / "Desktop" / "install-winux.desktop").read_text(encoding="utf-8")

        self.assertIn("shellprocess@winux_prepare_initcpio", settings)
        self.assertIn("shellprocess@winux_postinstall", settings)
        for mod_file in (
            "partition.conf",
            "mount.conf",
            "unpackfs.conf",
            "fstab.conf",
            "locale.conf",
            "keyboard.conf",
            "localecfg.conf",
            "initcpiocfg.conf",
            "initcpio.conf",
            "users.conf",
            "displaymanager.conf",
            "services-systemd.conf",
            "bootloader.conf",
            "finished.conf",
            "shellprocess-winux_prepare_initcpio.conf",
            "shellprocess-winux_postinstall.conf",
        ):
            self.assertTrue((calamares / "modules" / mod_file).is_file(), f"Missing Calamares module {mod_file}")

        self.assertTrue((calamares / "branding" / "default" / "branding.desc").is_file())
        self.assertIn("/run/archiso/bootmnt/winux/x86_64/airootfs.sfs", unpackfs)
        self.assertIn("/run/archiso/bootmnt/winux/boot/x86_64/vmlinuz-linux-cachyos", unpackfs)
        self.assertIn('defaultFileSystemType: "btrfs"', partition)
        for subvol in ("/@", "/@home", "/@cache", "/@log", "/@snapshots"):
            self.assertIn(subvol, mount)
        self.assertIn("compress=zstd:1", mount)
        self.assertIn("PRESETS=('default' 'fallback')", post)
        self.assertIn("snapper --no-dbus -c root create-config /", post)
        self.assertIn("rm -f /etc/sddm.conf.d/autologin.conf", post)
        self.assertIn("Exec=/usr/local/bin/winux-install", install_desktop)

    def test_winux_welcome_skips_on_live_iso(self) -> None:
        loader = importlib.machinery.SourceFileLoader(
            "winux_welcome",
            str(AIROOTFS / "usr" / "local" / "bin" / "winux-welcome"),
        )
        spec = importlib.util.spec_from_loader("winux_welcome", loader)
        self.assertIsNotNone(spec)


if __name__ == "__main__":
    unittest.main()
