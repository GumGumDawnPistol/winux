#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_SRC="${ROOT_DIR}/iso-profile"
WORK_DIR="${ROOT_DIR}/build/work"
OUT_DIR="${ROOT_DIR}/build/out"
STAGED_PROFILE="${ROOT_DIR}/build/profile"

CACHYOS_KEY_ID="F3B607488DB35A47"

run_as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

ensure_cachyos_key() {
  if ! grep -q '^\[cachyos\]' "${PROFILE_SRC}/pacman.conf"; then
    return 0
  fi

  if pacman-key --list-keys "${CACHYOS_KEY_ID}" >/dev/null 2>&1; then
    return 0
  fi

  echo "Importing CachyOS repository signing key (${CACHYOS_KEY_ID})..."
  if ! gpg --homedir /etc/pacman.d/gnupg --list-secret-keys 2>/dev/null | grep -q '^sec'; then
    run_as_root pacman-key --init
    run_as_root pacman-key --populate archlinux
  fi
  run_as_root pacman-key --recv-keys "${CACHYOS_KEY_ID}" --keyserver keyserver.ubuntu.com
  run_as_root pacman-key --lsign-key "${CACHYOS_KEY_ID}"
}

configure_staged_profile() {
  local systemd_etc="${STAGED_PROFILE}/airootfs/etc/systemd/system"

  find "${STAGED_PROFILE}" -type d -name "__pycache__" -exec rm -rf {} +

  # Remove releng units that conflict with NetworkManager and SDDM autologin
  rm -rf \
    "${systemd_etc}/getty@tty1.service.d" \
    "${systemd_etc}/multi-user.target.wants/iwd.service" \
    "${systemd_etc}/multi-user.target.wants/systemd-networkd.service" \
    "${systemd_etc}/network-online.target.wants/systemd-networkd-wait-online.service" \
    "${systemd_etc}/sockets.target.wants/systemd-networkd.socket"

  # Enable WINUX live services via systemd symlinks
  mkdir -p \
    "${systemd_etc}/multi-user.target.wants" \
    "${systemd_etc}/sysinit.target.wants"

  ln -sf /usr/lib/systemd/system/NetworkManager.service \
    "${systemd_etc}/multi-user.target.wants/NetworkManager.service"
  ln -sf /usr/lib/systemd/system/systemd-binfmt.service \
    "${systemd_etc}/sysinit.target.wants/systemd-binfmt.service"
  ln -sf /usr/lib/systemd/system/sddm.service \
    "${systemd_etc}/display-manager.service"

  # Point releng bootloader entries to linux-cachyos when selected
  if grep -qx 'linux-cachyos' "${STAGED_PROFILE}/packages.x86_64"; then
    rm -f "${STAGED_PROFILE}/airootfs/etc/mkinitcpio.d/linux.preset"
    local boot_dir
    for boot_dir in efiboot syslinux grub; do
      if [[ -d "${STAGED_PROFILE}/${boot_dir}" ]]; then
        find "${STAGED_PROFILE}/${boot_dir}" -type f \( -name '*.conf' -o -name '*.cfg' \) -exec \
          sed -i \
            -e 's/Arch Linux install medium/WINUX Live Desktop (Boot without installing)/g' \
            -e 's/vmlinuz-linux\b/vmlinuz-linux-cachyos/g' \
            -e 's/initramfs-linux\.img\b/initramfs-linux-cachyos.img/g' \
            -e '/^options / s/$/ cow_spacesize=4G/' \
            -e '/^[[:space:]]*linux .*archisobasedir=/ s/$/ cow_spacesize=4G/' \
            -e '/^[[:space:]]*APPEND .*archisobasedir=/ s/$/ cow_spacesize=4G/' {} +
      fi
    done

    local efi_entries="${STAGED_PROFILE}/efiboot/loader/entries"
    if [[ -f "${efi_entries}/01-archiso-x86_64-linux.conf" ]]; then
      cp "${efi_entries}/01-archiso-x86_64-linux.conf" "${efi_entries}/02-winux-x86_64-ram.conf"
      sed -i \
        -e 's/WINUX Live Desktop (Boot without installing)/WINUX Live Desktop (Boot to RAM without installing)/g' \
        -e '/^options / s/$/ copytoram=y/' \
        "${efi_entries}/02-winux-x86_64-ram.conf"
    fi
  fi
}

build_native() {
  if ! command -v mkarchiso >/dev/null 2>&1; then
    echo "mkarchiso not found. Run on Arch/CachyOS or use --container." >&2
    exit 1
  fi

  ensure_cachyos_key

  rm -rf "${STAGED_PROFILE}" "${WORK_DIR}"
  mkdir -p "${STAGED_PROFILE}" "${OUT_DIR}"

  # Start from upstream archiso releng baseline, then apply WINUX overlays
  cp -a /usr/share/archiso/configs/releng/. "${STAGED_PROFILE}/"
  cp -a "${PROFILE_SRC}/." "${STAGED_PROFILE}/"

  configure_staged_profile

  run_as_root mkarchiso -v -w "${WORK_DIR}" -o "${OUT_DIR}" "${STAGED_PROFILE}"
}

build_container() {
  local runtime=""
  if command -v podman >/dev/null 2>&1; then
    runtime="podman"
  elif command -v docker >/dev/null 2>&1; then
    runtime="docker"
  else
    echo "Neither podman nor docker was found." >&2
    exit 1
  fi

  "${runtime}" run --rm --privileged \
    -v "${ROOT_DIR}:/winux" \
    -w /winux \
    archlinux:latest \
    bash -c '
      pacman -Syu --noconfirm archiso && \
      ./scripts/build-iso.sh
    '
}

if [[ "${1:-}" == "--container" ]]; then
  build_container
else
  build_native
fi
