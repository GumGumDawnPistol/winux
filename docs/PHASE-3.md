# Phase 3: Windows 10 KDE Plasma 6 Theme & UX

**Goal:** Deliver a familiar Windows 10 desktop layout, visual identity, and keyboard ergonomics on **KDE Plasma 6 (Wayland)** without sacrificing VRR/HDR gaming support or native Linux flexibility.

---

## 1. Implemented Deliverables

- **Visual Assets:**
  - [`winux-start.svg`](../iso-profile/airootfs/usr/share/icons/winux/winux-start.svg) — Custom 4-pane WINUX Start icon (`#0078D7` accent).
  - [`winux-hero.svg`](../iso-profile/airootfs/usr/share/wallpapers/winux/winux-hero.svg) — Dark-blue geometric hero wallpaper.
- **KDE Plasma 6 Defaults (`etc/skel/.config/`):**
  - [`kdeglobals`](../iso-profile/airootfs/etc/skel/.config/kdeglobals) — Breeze Dark theme, `#0078D7` window accent frame, and Windows-style double-click (`SingleClick=false`).
  - [`kwinrc`](../iso-profile/airootfs/etc/skel/.config/kwinrc) — Borderless maximized windows and standard Windows titlebar buttons (`ButtonsOnLeft=M`, `ButtonsOnRight=IAX`).
  - [`kglobalshortcutsrc`](../iso-profile/airootfs/etc/skel/.config/kglobalshortcutsrc) — `Win+E` (Dolphin), `Win+R` (KRunner), `Win+L` (Lock), `Win+D` (Show Desktop), `Win+Tab` (Overview), `Win+Left/Right/Up/Down` (Window snap/maximize/minimize), and `Ctrl+Shift+Esc` (System Monitor).
- **Taskbar & First-Login Layout Script:**
  - [`plasma-win10-layout.js`](../iso-profile/airootfs/usr/local/share/winux/plasma-win10-layout.js) — Builds a `44px` bottom taskbar with Kickoff Start Menu, KRunner search, pinned Icons-Only Task Manager (`Dolphin`, `Konsole`, `WINUX Manager`, `Steam`), System Tray, `12h` + short-date Digital Clock, and far-right Show Desktop peek strip.
  - [`winux-apply-theme`](../iso-profile/airootfs/usr/local/bin/winux-apply-theme) & [`winux-apply-theme.desktop`](../iso-profile/airootfs/etc/skel/.config/autostart/winux-apply-theme.desktop) — Idempotent first-login applier (`~/.config/winux/theme-applied`, resettable via `--force`).
- **Systemd Service Presets:**
  - [`10-winux.preset`](../iso-profile/airootfs/etc/systemd/system-preset/10-winux.preset) — Enables `sddm`, `NetworkManager`, `systemd-binfmt`, and `snapper` timers.
