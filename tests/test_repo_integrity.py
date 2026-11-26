"""Repository-wide integrity checks across all WINUX phases."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ISO_PROFILE = REPO_ROOT / "iso-profile"
AIROOTFS = ISO_PROFILE / "airootfs"

_LF_CHECK_SUFFIXES = {".sh", ".conf", ".desktop", ".preset", ".x86_64", ".js", ".svg"}


class RepoIntegrityTests(unittest.TestCase):
    def test_no_crlf_in_linux_files(self) -> None:
        bin_dir = AIROOTFS / "usr" / "local" / "bin"
        checked = 0
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix in _LF_CHECK_SUFFIXES or path.parent == bin_dir:
                raw = path.read_bytes()
                self.assertNotIn(b"\r\n", raw, f"CRLF line ending found in {path}")
                checked += 1
        self.assertGreater(checked, 15)

    def test_no_pycache_inside_airootfs(self) -> None:
        caches = list(ISO_PROFILE.rglob("__pycache__"))
        self.assertEqual(caches, [], f"Remove __pycache__ from iso-profile: {caches}")

    def test_all_local_bin_executables_listed_in_profiledef(self) -> None:
        profiledef = (ISO_PROFILE / "profiledef.sh").read_text(encoding="utf-8")
        bin_dir = AIROOTFS / "usr" / "local" / "bin"
        for exe in bin_dir.iterdir():
            if exe.is_file():
                expected = f'["/usr/local/bin/{exe.name}"]="0:0:755"'
                self.assertIn(expected, profiledef, f"Missing executable permission in profiledef.sh: {expected}")

    def test_json_files_parse_cleanly(self) -> None:
        for path in (REPO_ROOT / ".vscode").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))

    def test_desktop_files_have_required_keys(self) -> None:
        for desktop in AIROOTFS.rglob("*.desktop"):
            text = desktop.read_text(encoding="utf-8")
            self.assertIn("[Desktop Entry]", text, f"Missing header in {desktop}")
            self.assertRegex(text, re.compile(r"^Name=.+$", re.MULTILINE), f"Missing Name= in {desktop}")
            self.assertRegex(text, re.compile(r"^Exec=.+$", re.MULTILINE), f"Missing Exec= in {desktop}")

    def test_build_script_configures_live_boot_without_install(self) -> None:
        build_sh = (REPO_ROOT / "scripts" / "build-iso.sh").read_text(encoding="utf-8")
        self.assertIn("WINUX Live Desktop (Boot without installing)", build_sh)
        self.assertIn("copytoram=y", build_sh)
        self.assertIn("cow_spacesize=4G", build_sh)


if __name__ == "__main__":
    unittest.main()
