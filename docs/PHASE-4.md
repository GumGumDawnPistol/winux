# Phase 4: Calamares Btrfs/Snapper Installer & First-Boot Wizard

**Goal:** Turn WINUX into an installable OS with automatic **Btrfs subvolumes + Snapper snapshots** and a **First-Boot Welcome Wizard** that handles NVIDIA drivers, Flathub, gaming tools, and Windows `.exe` runtime initialization.

---

## 1. Implemented Deliverables

- **Calamares Installer Configuration (`iso-profile/airootfs/etc/calamares/`):**
  - [`settings.conf`](../iso-profile/airootfs/etc/calamares/settings.conf) — Full GUI install sequence including `shellprocess@winux_postinstall`.
  - [`modules/partition.conf`](../iso-profile/airootfs/etc/calamares/modules/partition.conf) — Defaults to `btrfs` with swap options.
  - [`modules/mount.conf`](../iso-profile/airootfs/etc/calamares/modules/mount.conf) — Configures Btrfs subvolumes (`/@`, `/@home`, `/@cache`, `/@log`, `/@snapshots`) with `compress=zstd:1,noatime,space_cache=v2`.
  - [`modules/bootloader.conf`](../iso-profile/airootfs/etc/calamares/modules/bootloader.conf) — Configures `systemd-boot` targeting `vmlinuz-linux-cachyos`.
  - [`modules/shellprocess-winux_postinstall.conf`](../iso-profile/airootfs/etc/calamares/modules/shellprocess-winux_postinstall.conf) & [`winux-postinstall`](../iso-profile/airootfs/usr/local/bin/winux-postinstall) — Removes Live ISO autologin, cleans up the Live desktop installer shortcut, initializes Snapper (`snapper -c root create-config /`), and enables system presets.
  - [`install-winux.desktop`](../iso-profile/airootfs/etc/skel/Desktop/install-winux.desktop) — Live Desktop installer launcher (`pkexec calamares`).
- **First-Boot Wizard (`winux_setup` + `winux-welcome`):**
  - [`hardware.py`](../iso-profile/airootfs/usr/local/lib/winux_setup/hardware.py) — Detects GPU vendors (`0x10de` NVIDIA, `0x1002` AMD, `0x8086` Intel), `/dev/ntsync`, and Live ISO state (`/run/archiso`).
  - [`tasks.py`](../iso-profile/airootfs/usr/local/lib/winux_setup/tasks.py) — Generates setup tasks (NVIDIA drivers, Flathub, Heroic + ProtonUp-Qt Flatpaks, `winux-exec` default prefix runtimes) and persists `~/.config/winux/first-boot.json`.
  - [`winux-welcome`](../iso-profile/airootfs/usr/local/bin/winux-welcome) & [`winux-welcome.desktop`](../iso-profile/airootfs/etc/skel/.config/autostart/winux-welcome.desktop) — PySide6 first-boot GUI (auto-skipped on Live ISO).
- **Note on Calamares Packaging:** Add `calamares` (from CachyOS/custom repo or AUR build) when assembling the final Live ISO image if not already present in your configured mirror.
