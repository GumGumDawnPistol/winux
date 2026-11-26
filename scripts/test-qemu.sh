#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_PATH="$(ls -1t "${ROOT_DIR}"/build/out/winux-*.iso 2>/dev/null | head -n 1 || true)"

if [[ -z "${ISO_PATH}" ]]; then
  echo "No WINUX ISO found in ${ROOT_DIR}/build/out/. Run ./scripts/build-iso.sh first." >&2
  exit 1
fi

if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
  echo "qemu-system-x86_64 not found." >&2
  exit 1
fi

KVM_FLAG=()
if [[ -e /dev/kvm ]]; then
  KVM_FLAG=(-enable-kvm -cpu host)
fi

OVMF_CODE=""
for candidate in \
  /usr/share/edk2/x64/OVMF_CODE.4m.fd \
  /usr/share/edk2-ovmf/x64/OVMF_CODE.4m.fd \
  /usr/share/OVMF/OVMF_CODE_4M.fd \
  /usr/share/OVMF/OVMF_CODE.fd; do
  if [[ -f "${candidate}" ]]; then
    OVMF_CODE="${candidate}"
    break
  fi
done

BIOS_FLAGS=()
if [[ -n "${OVMF_CODE}" ]]; then
  BIOS_FLAGS=(-drive "if=pflash,format=raw,readonly=on,file=${OVMF_CODE}")
else
  echo "Warning: OVMF firmware not found; falling back to legacy BIOS boot." >&2
fi

echo "Booting ${ISO_PATH} in QEMU..."
exec qemu-system-x86_64 \
  "${KVM_FLAG[@]}" \
  "${BIOS_FLAGS[@]}" \
  -m 4096 \
  -smp 4 \
  -vga virtio \
  -display default,gl=on \
  -cdrom "${ISO_PATH}" \
  -boot d
