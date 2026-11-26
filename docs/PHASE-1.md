# Phase 1: Base ISO, Kernel & `.exe` Foundation

**Goal:** Produce a bootable x86_64 WINUX Live ISO built on **Arch / CachyOS**, booting into **KDE Plasma 6 (Wayland)** with **`/dev/ntsync`**, **`binfmt_misc` `.exe` execution**, and **Btrfs + Snapper** tooling ready for installation and VM verification.

---

## 1. Completed Scaffolding & Live Configuration

- [x] **Project & VS Code Setup:** Configured [`.vscode/settings.json`](../.vscode/settings.json), [`.vscode/extensions.json`](../.vscode/extensions.json), [`.gitattributes`](../.gitattributes) (`LF` line endings for Linux scripts/configs), and [`.gitignore`](../.gitignore).
- [x] **Architecture & Overview:** Documented system layers and 4-phase roadmap in [`README.md`](../README.md) and [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).
- [x] **Archiso Profile & Repositories:**
  - Configured [`iso-profile/profiledef.sh`](../iso-profile/profiledef.sh) (UEFI/BIOS boot modes, zstd squashfs, file permissions including `/etc/shadow`, `/etc/gshadow`, and `/etc/sudoers.d/winux`).
  - Added [`iso-profile/pacman.conf`](../iso-profile/pacman.conf) enabling `[cachyos]` and `[multilib]`.
  - Updated [`iso-profile/packages.x86_64`](../iso-profile/packages.x86_64) with `linux-cachyos`, `linux-cachyos-headers`, `cachyos-keyring`, `cachyos-mirrorlist`, `vulkan-tools`, `lib32-*` Vulkan/Mesa/MangoHud/GameMode stacks, `steam`, `umu-launcher`, and `proton-cachyos`.
- [x] **Kernel & Gaming Tuning:**
  - Autoload `ntsync` via [`iso-profile/airootfs/etc/modules-load.d/ntsync.conf`](../iso-profile/airootfs/etc/modules-load.d/ntsync.conf).
  - Set `vm.max_map_count = 2147483642` via [`iso-profile/airootfs/etc/sysctl.d/99-winux-gaming.conf`](../iso-profile/airootfs/etc/sysctl.d/99-winux-gaming.conf).
  - Added `mkinitcpio` preset [`iso-profile/airootfs/etc/mkinitcpio.d/linux-cachyos.preset`](../iso-profile/airootfs/etc/mkinitcpio.d/linux-cachyos.preset).
- [x] **Live Session Configuration (`airootfs/`):**
  - Added `winux` live user (password `winux`) and passwordless `sudo` via [`passwd`](../iso-profile/airootfs/etc/passwd), [`group`](../iso-profile/airootfs/etc/group), [`shadow`](../iso-profile/airootfs/etc/shadow), [`gshadow`](../iso-profile/airootfs/etc/gshadow), and [`sudoers.d/winux`](../iso-profile/airootfs/etc/sudoers.d/winux).
  - Configured SDDM Plasma 6 Wayland autologin in [`iso-profile/airootfs/etc/sddm.conf.d/autologin.conf`](../iso-profile/airootfs/etc/sddm.conf.d/autologin.conf).
  - Added zram swap config in [`iso-profile/airootfs/etc/systemd/zram-generator.conf`](../iso-profile/airootfs/etc/systemd/zram-generator.conf) and PipeWire defaults in [`10-winux-gaming.conf`](../iso-profile/airootfs/etc/pipewire/pipewire.conf.d/10-winux-gaming.conf).
- [x] **Windows `.exe` / `.msi` Dispatch Layer:**
  - Registered PE (`MZ`) magic bytes via [`iso-profile/airootfs/etc/binfmt.d/winux-exe.conf`](../iso-profile/airootfs/etc/binfmt.d/winux-exe.conf).
  - Added XDG MIME entry [`winux-exec.desktop`](../iso-profile/airootfs/usr/share/applications/winux-exec.desktop) and default associations in [`mimeapps.list`](../iso-profile/airootfs/etc/xdg/mimeapps.list).
  - Implemented [`iso-profile/airootfs/usr/local/bin/winux-exec`](../iso-profile/airootfs/usr/local/bin/winux-exec) with `PROTON_USE_NTSYNC=1` detection, isolated prefixes (`~/.local/share/winux/prefixes/`), `.msi` support, and `--game` / `--gamescope` flags.
- [x] **Build & VM Scripts:** Updated [`scripts/build-iso.sh`](../scripts/build-iso.sh) (CachyOS key import, systemd service symlinks for `NetworkManager` / `sddm` / `systemd-binfmt`, `linux-cachyos` bootloader entry rewrite, root/sudo container support) and [`scripts/test-qemu.sh`](../scripts/test-qemu.sh) (multi-distro OVMF detection).

---

## 2. Remaining Tasks to Finish Phase 1 (Requires Linux / WSL2 / Container Host)

- [ ] **Shellcheck Lint:** Run `shellcheck scripts/*.sh iso-profile/profiledef.sh` inside WSL2/Linux (`shellcheck` is not installed on the current Windows host).
- [ ] **First ISO Build:** Execute `./scripts/build-iso.sh --container` (from WSL2/Linux with Docker or Podman) or `./scripts/build-iso.sh` on an Arch/CachyOS host.
- [ ] **QEMU Boot & Smoke Test:** Boot the generated ISO via `./scripts/test-qemu.sh` and verify all Phase 1 acceptance checks below.

---

## 3. Phase 1 Acceptance Criteria

| Check | Expected Result |
| :--- | :--- |
| **ISO Boot** | ISO boots cleanly in UEFI (OVMF) and lands in a KDE Plasma 6 Wayland desktop (`winux` autologin). |
| **Kernel & `ntsync`** | `uname -r` reports Linux `6.14+` (`-cachyos`) and `ls -l /dev/ntsync` exists. |
| **`binfmt_misc`** | `cat /proc/sys/fs/binfmt_misc/winux-exe` shows `enabled` pointing to `/usr/local/bin/winux-exec`. |
| **`.exe` Execution** | Running a sample Windows `.exe` directly (`./test.exe` or double-click in Dolphin) launches via `winux-exec`. |
| **Audio & Graphics** | PipeWire audio (`wpctl status`) and Vulkan (`vulkaninfo --summary`) initialize without errors. |

---

## 4. Handoff to Next Phases
- **Phase 2:** Expand `winux-exec` with automatic Windows dependency bootstrapping (VC++ / `.NET`), Start Menu `.desktop` shortcut generation for installed apps, and a GUI compatibility/prefix manager.
- **Phase 3:** Package the **Windows 10 KDE Plasma 6 theme** (bottom taskbar, Start Menu widget, icons, fonts, and `Win+*` shortcuts) under `airootfs/etc/skel/`.
- **Phase 4:** Integrate **Calamares** installer with Btrfs subvolumes (`@`, `@home`, `@cache`, `@log`) + Snapper bootable snapshots and first-boot driver/store setup.
