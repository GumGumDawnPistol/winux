#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="winux"
iso_label="WINUX_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="WINUX Project"
iso_application="WINUX Gaming & Windows-Compatible Linux OS"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="winux"
buildmodes=('iso')
bootmodes=(
  'bios.syslinux.mbr'
  'bios.syslinux.eltorito'
  'uefi-ia32.systemd-boot.esp'
  'uefi-x64.systemd-boot.esp'
  'uefi-ia32.systemd-boot.eltorito'
  'uefi-x64.systemd-boot.eltorito'
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15' '-b' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/etc/sudoers.d"]="0:0:750"
  ["/etc/sudoers.d/winux"]="0:0:440"
  ["/root"]="0:0:750"
  ["/usr/local/bin/winux-exec"]="0:0:755"
  ["/usr/local/bin/winux-manager"]="0:0:755"
  ["/usr/local/bin/winux-apply-theme"]="0:0:755"
  ["/usr/local/bin/winux-welcome"]="0:0:755"
  ["/usr/local/bin/winux-postinstall"]="0:0:755"
)
