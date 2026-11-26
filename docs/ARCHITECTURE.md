# WINUX Architecture & Roadmap

## 1. Base OS & Update Safety
- **Distribution Base:** Arch Linux with CachyOS-optimized repositories (`x86-64-v3` / `v4` where supported) for lower latency and faster frame times.
- **Filesystem & Recovery:** **Btrfs** root subvolumes (`@`, `@home`, `@cache`, `@log`) paired with **Snapper** and boot-menu snapshot entries (GRUB/Limine) so rolling updates remain safely reversible.
- **Kernel:** `linux-cachyos` (6.14+ with **BORE scheduler** and **`ntsync`** module `/dev/ntsync`).

## 2. How Windows `.exe` Files Run Seamlessly
WINUX does not emulate a full Windows VM for standard apps and games. Instead, it embeds translation directly into the OS:

1. **Kernel Recognition (`binfmt_misc`):**
   - `/etc/binfmt.d/winux-exe.conf` registers the Windows PE magic bytes (`MZ`) to `/usr/local/bin/winux-exec`.
   - Running `./Setup.exe` in a terminal or double-clicking an `.exe` in Dolphin invokes `winux-exec` automatically.
2. **XDG Desktop Integration:**
   - `/usr/share/applications/winux-exec.desktop` handles `application/x-ms-dos-executable` and `application/x-msi` so file managers and browsers open Windows binaries with one click.
3. **Smart Dispatch (`winux-exec`):**
   - **Games (`--game` / game-prefix routing):** Launches through **`umu-launcher`** (`umu-run`) with **GE-Proton**, **DXVK**, **VKD3D-Proton**, **GameMode**, and optional **Gamescope** (for FSR upscaling, HDR, and frame-rate capping).
   - **Desktop Apps & Installers:** Routes through isolated per-app or shared Wine prefixes (`~/.local/share/winux/prefixes/`), enabling `/dev/ntsync` when available and helping provision common dependencies (VC++ Redistributables, `.NET`, core fonts).
4. **Known Boundary — Kernel Anti-Cheat:**
   - User-space / Proton-supported anti-cheats (e.g., Easy Anti-Cheat and BattlEye when enabled by the game developer) work on Linux.
   - Windows kernel-mode anti-cheats (e.g., Riot Vanguard, Ricochet) **cannot** run natively inside Linux/Wine. WINUX compatibility checks should surface this clearly to the user.

## 3. Windows 10 Desktop Experience (KDE Plasma 6)
- **Compositor:** KWin on **Wayland** (VRR/FreeSync/G-Sync, HDR, fractional scaling, XWayland for legacy/Wine apps).
- **Layout & Theme Targets:**
  - Bottom `44px` taskbar with Icons-Only Task Manager and system tray clock (`MM/DD/YYYY`).
  - Windows-10-style Start Menu widget (grid + categorized app list) and Start icon.
  - Windows-familiar shortcuts (`Win+E` file manager, `Win+R` KRunner, `Win+L` lock, `Ctrl+Shift+Esc` system monitor).
  - Unified app menu showing both native Linux apps (Flatpak + `pacman`) and installed Windows `.exe` apps.

## 4. Implementation Roadmap

### Phase 1 — Bootable Base ISO & Kernel Tuning
- Validate `iso-profile/` with `mkarchiso` in an Arch container or VM.
- Verify `/dev/ntsync`, PipeWire audio, Wayland KDE Plasma 6 session, and GPU driver detection (AMD/Intel Mesa + NVIDIA).

### Phase 2 — `.exe` Subsystem (`winux-exec` + Prefix Manager)
- Expand `winux-exec` into a full prefix manager (auto-detect game vs. desktop app, shortcut `.desktop` generator for installed Windows programs, Winetricks/dependency bootstrapping).
- Add a lightweight GUI prompt/settings dialog (e.g., PySide6/QML) for per-app runner selection, Gamescope toggles, and ProtonDB/anti-cheat warnings.

### Phase 3 — Windows 10 Theme Package (`winux-theme-win10`)
- Package Plasma 6 Look-and-Feel, icon pack, Aurorae/Breeze window decorations, panel layout script (`plasma-apply-lookandfeel`), and default `kglobalshortcutsrc` into `airootfs/etc/skel/`.

### Phase 4 — Installer & First-Boot Wizard
- Integrate **Calamares** with automatic Btrfs + Snapper subvolume layout.
- Add a first-boot welcome wizard for GPU drivers, Steam/Heroic/Flatpak setup, and `.exe` compatibility defaults.
