# Phase 2: Windows `.exe` Compatibility & Prefix Manager

**Goal:** Turn `winux-exec` from a minimal wrapper into a full OS-level `.exe` / `.msi` compatibility subsystem with isolated prefixes, runtime bootstrapping, automatic Start Menu `.desktop` shortcuts, and a native KDE/Qt6 GUI manager.

---

## 1. Implemented Deliverables

- **Core Library (`winux_compat`)** under [`iso-profile/airootfs/usr/local/lib/winux_compat/`](../iso-profile/airootfs/usr/local/lib/winux_compat/__init__.py):
  - [`config.py`](../iso-profile/airootfs/usr/local/lib/winux_compat/config.py): XDG prefix/application/state paths, sanitized prefix names, and persistent `winux-prefix.json` configuration (`mode`, `runner`, `gamemode`, `gamescope`, `mangohud`, `ntsync`, `installed_deps`).
  - [`detector.py`](../iso-profile/airootfs/usr/local/lib/winux_compat/detector.py): Pure-Python PE header parser (`x86`, `x64`, `arm64`, `gui`/`console`) and heuristic classifier (`game`, `app`, `installer`).
  - [`prefixes.py`](../iso-profile/airootfs/usr/local/lib/winux_compat/prefixes.py): Isolated prefix lifecycle (`ensure_prefix`, `list_prefixes`, `remove_prefix`) and `winetricks` dependency bootstrapping (`vcrun2022`, `corefonts`, `dotnet48`, `dxvk`) with idempotent tracking.
  - [`runner.py`](../iso-profile/airootfs/usr/local/lib/winux_compat/runner.py): Runtime environment builder (`PROTON_USE_NTSYNC=1` when `/dev/ntsync` exists, `WINEFSYNC=1` fallback), `umu-run` / `wine` / `msiexec` command selection, `gamemoderun` + `gamescope` wrapping, and launch logging.
  - [`shortcuts.py`](../iso-profile/airootfs/usr/local/lib/winux_compat/shortcuts.py): Scans installed Windows programs inside a prefix, extracts `.exe` icons via `icoutils` (`wrestool` + `icotool`) when available, and generates Start Menu `.desktop` entries.
- **CLI Dispatcher ([`winux-exec`](../iso-profile/airootfs/usr/local/bin/winux-exec)):**
  - Direct execution (from `binfmt_misc`, Dolphin, or terminal): `winux-exec /path/to/app.exe`
  - Inspection & management flags: `--inspect FILE`, `--list`, `--deps VERB... --prefix NAME`, `--scan-shortcuts --prefix NAME`, `--game`, `--gamescope`, `--mangohud`, `--runner`.
- **Qt6 Compatibility Manager ([`winux-manager`](../iso-profile/airootfs/usr/local/bin/winux-manager)):**
  - GUI application ([`winux-manager.desktop`](../iso-profile/airootfs/usr/share/applications/winux-manager.desktop)) for creating/deleting prefixes, toggling Gamescope/GameMode/MangoHud, installing Windows runtimes, launching `.exe`/`.msi` installers, and generating Start Menu shortcuts.
- **Archiso Integration:** Added `pyside6` and `icoutils` to [`packages.x86_64`](../iso-profile/packages.x86_64) and executable permissions in [`profiledef.sh`](../iso-profile/profiledef.sh).
- **Automated Tests:** [`tests/test_winux_compat.py`](../tests/test_winux_compat.py).

---

## 2. Verification Commands

Run the unit test suite locally on Windows or Linux:

```bash
python -m unittest discover -s tests -v
```
