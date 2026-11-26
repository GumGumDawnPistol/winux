# Phase 4: Calamares Btrfs/Snapper Installer & First-Boot Wizard

**Goal:** Turn WINUX into an installable OS with automatic **Btrfs subvolumes + Snapper snapshots** and a **First-Boot Welcome Wizard** that handles NVIDIA drivers, Flathub, gaming tools, and Windows `.exe` runtime initialization.

---

## 1. Implemented Deliverables

- **Calamares Installer Configuration (`iso-profile/airootfs/etc/calamares/`):**
  - [`settings.conf`](../iso-profile/airootfs/etc/calamares/settings.conf) — Full GUI install sequence including `shellprocess@winux_prepare_initcpio` and `shellprocess@winux_postinstall`.
  - [`modules/partition.conf`](../iso-profile/airootfs/etc/calamares/modules/partition.conf) & [`modules/mount.conf`](../iso-profile/airootfs/etc/calamares/modules/mount.conf) — Defaults to `btrfs` subvolumes (`/@`, `/@home`, `/@cache`, `/@log`, `/@snapshots`) with `compress=zstd:1,noatime,space_cache=v2`.
  - [`modules/unpackfs.conf`](../iso-profile/airootfs/etc/calamares/modules/unpackfs.conf) — Unpacks `/run/archiso/bootmnt/winux/x86_64/airootfs.sfs` and copies `vmlinuz-linux-cachyos` to `/boot/`.
  - [`modules/bootloader.conf`](../iso-profile/airootfs/etc/calamares/modules/bootloader.conf), [`modules/users.conf`](../iso-profile/airootfs/etc/calamares/modules/users.conf), [`modules/displaymanager.conf`](../iso-profile/airootfs/etc/calamares/modules/displaymanager.conf), [`modules/initcpiocfg.conf`](../iso-profile/airootfs/etc/calamares/modules/initcpiocfg.conf), [`modules/initcpio.conf`](../iso-profile/airootfs/etc/calamares/modules/initcpio.conf), [`modules/services-systemd.conf`](../iso-profile/airootfs/etc/calamares/modules/services-systemd.conf), [`modules/fstab.conf`](../iso-profile/airootfs/etc/calamares/modules/fstab.conf), [`modules/finished.conf`](../iso-profile/airootfs/etc/calamares/modules/finished.conf), [`branding/default/branding.desc`](../iso-profile/airootfs/etc/calamares/branding/default/branding.desc).
  - [`winux-postinstall`](../iso-profile/airootfs/usr/local/bin/winux-postinstall) — Restores disk `mkinitcpio` presets (`--prepare-initcpio`), removes Live ISO autologin/desktop shortcut, initializes Snapper (`snapper -c root create-config /`), and enables system presets.
  - [`winux-install`](../iso-profile/airootfs/usr/local/bin/winux-install) & [`install-winux.desktop`](../iso-profile/airootfs/etc/skel/Desktop/install-winux.desktop) — Wayland-preserving `pkexec` launcher for `cachyos-calamares`.
- **First-Boot Wizard (`winux_setup` + `winux-welcome`):**
  - [`hardware.py`](../iso-profile/airootfs/usr/local/lib/winux_setup/hardware.py) — Detects GPU vendors (`0x10de` NVIDIA, `0x1002` AMD, `0x8086` Intel), `/dev/ntsync`, and Live ISO state (`/run/archiso`).
  - [`tasks.py`](../iso-profile/airootfs/usr/local/lib/winux_setup/tasks.py) — Generates setup tasks (NVIDIA drivers, Flathub, Heroic + ProtonUp-Qt Flatpaks, `winux-exec` default prefix runtimes) and persists `~/.config/winux/first-boot.json`.
  - [`winux-welcome`](../iso-profile/airootfs/usr/local/bin/winux-welcome) & [`winux-welcome.desktop`](../iso-profile/airootfs/etc/skel/.config/autostart/winux-welcome.desktop) — PySide6 first-boot GUI (auto-skipped on Live ISO).
- **Installer Package:** `cachyos-calamares` is included from `[cachyos]` in [`packages.x86_64`](../iso-profile/packages.x86_64).
