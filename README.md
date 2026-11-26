# WINUX

A gaming-focused, **Arch / CachyOS-based Linux OS** with a **Windows 10–inspired KDE Plasma 6 desktop** and built-in, seamless **Windows `.exe` / `.msi` execution** for both games and desktop applications—while keeping the full Linux system open and unrestricted.

## Core Pillars

1. **Unrestricted Linux Foundation:** Arch / CachyOS base with `pacman`, AUR support, Flatpak (Flathub), and **Btrfs + Snapper** snapshots for safe rollbacks.
2. **Kernel-Level Performance:** Linux 6.14+ gaming kernel (`linux-cachyos` / BORE scheduler) with upstream **`/dev/ntsync`** enabled for low-overhead Windows thread synchronization.
3. **Seamless `.exe` Execution:** Kernel `binfmt_misc` registration + XDG MIME integration routed through `winux-exec` (**Wine + GE-Proton + DXVK + VKD3D-Proton + `umu-launcher`**).
4. **Windows 10 UX on Wayland:** **KDE Plasma 6** configured with a Windows 10 taskbar, Start Menu layout, icon pack, and familiar shortcuts (`Win+E`, `Win+R`, `Win+X`), paired with VRR/HDR gaming support.

## Repository Layout

```text
WINUX/
├── .vscode/                   # VS Code settings (enforces LF line endings for Linux scripts)
├── docs/
│   ├── ARCHITECTURE.md        # Detailed OS design, compatibility boundaries, and roadmap
│   ├── PHASE-1.md             # Phase 1 checklist, remaining tasks, and acceptance criteria
│   ├── PHASE-2.md             # Phase 2 Windows compatibility & prefix manager deliverables
│   ├── PHASE-3.md             # Phase 3 Windows 10 KDE Plasma 6 theme & UX
│   └── PHASE-4.md             # Phase 4 Calamares Btrfs/Snapper installer & first-boot wizard
├── tests/                     # Unit tests for winux_compat
├── iso-profile/               # archiso build profile
│   ├── profiledef.sh          # ISO metadata & file permissions
│   ├── packages.x86_64        # Curated base, kernel, Plasma 6, and gaming/Wine packages
│   └── airootfs/              # Root filesystem overlays (binfmt_misc, ntsync, sysctl, winux-exec)
└── scripts/
    ├── build-iso.sh           # Build bootable WINUX ISO (native Arch or Docker/Podman)
    └── test-qemu.sh           # Boot the generated ISO in QEMU/OVMF
```

## Quick Start (Building & Testing)

Because `mkarchiso` requires Linux tools (`pacman`, `mksquashfs`), build from **Arch/CachyOS**, **WSL2 (Arch)**, or **Docker/Podman**:

```bash
# Build the bootable ISO (Linux / WSL2 / Docker / Podman)
./scripts/build-iso.sh --container

# Or trigger the GitHub Actions workflow `.github/workflows/build-iso.yml`
# and download `winux-iso-x86_64` from the Actions Artifacts tab.

# Test the ISO in QEMU (UEFI)
./scripts/test-qemu.sh
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design and implementation roadmap.
