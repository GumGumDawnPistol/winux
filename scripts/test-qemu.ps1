<#
.SYNOPSIS
    Boot the built WINUX ISO in QEMU (UEFI) on Windows.
#>
param(
    [int]$MemoryMB = 4096,
    [int]$CpuCores = 4,
    [switch]$ForceTCG
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$IsoFile = Get-ChildItem -Path (Join-Path $RootDir "build\out") -Filter "winux-*.iso" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $IsoFile) {
    throw "No WINUX ISO found in '$RootDir\build\out'."
}

$QemuExe = "C:\Program Files\qemu\qemu-system-x86_64.exe"
$QemuImg = "C:\Program Files\qemu\qemu-img.exe"
$OvmfCode = "C:\Program Files\qemu\share\edk2-x86_64-code.fd"

if (-not (Test-Path $QemuExe)) {
    throw "QEMU not found at '$QemuExe'."
}

$VmDir = Join-Path $RootDir "build\vm"
New-Item -ItemType Directory -Force -Path $VmDir | Out-Null
$DiskPath = Join-Path $VmDir "winux-disk.qcow2"
if (-not (Test-Path $DiskPath)) {
    & $QemuImg create -f qcow2 $DiskPath 32G | Out-Null
}

$AccelArgs = @("-accel", "tcg,thread=multi", "-cpu", "max")
if (-not $ForceTCG) {
    # Probe whether Windows Hypervisor Platform (WHPX) is active on this host
    $probe = Start-Process -FilePath $QemuExe -ArgumentList "-accel", "whpx", "-display", "none", "-S", "-no-reboot" -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 600
    if (-not $probe.HasExited) {
        $probe.Kill()
        $AccelArgs = @("-accel", "whpx", "-cpu", "host")
    } elseif ($probe.ExitCode -eq 0) {
        $AccelArgs = @("-accel", "whpx", "-cpu", "host")
    }
}

$ArgsList = @(
    "-name", "WINUX-VM",
    "-machine", "q35"
) + $AccelArgs + @(
    "-m", "$MemoryMB",
    "-smp", "$CpuCores",
    "-drive", "if=pflash,format=raw,readonly=on,file=$OvmfCode",
    "-drive", "file=$DiskPath,format=qcow2,if=virtio",
    "-cdrom", $IsoFile.FullName,
    "-boot", "order=d",
    "-vga", "virtio",
    "-display", "sdl",
    "-device", "qemu-xhci",
    "-device", "usb-tablet",
    "-nic", "user,model=virtio-net-pci"
)

Write-Host "Starting WINUX VM ($($AccelArgs[1])) with ISO: $($IsoFile.FullName)"
$QuotedArgs = ($ArgsList | ForEach-Object {
    if ($_ -match '\s') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
}) -join ' '
$LogFile = Join-Path $VmDir "qemu-stderr.log"
Start-Process -FilePath $QemuExe -ArgumentList $QuotedArgs -RedirectStandardError $LogFile -WindowStyle Normal | Out-Null
