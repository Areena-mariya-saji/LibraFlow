#!/usr/bin/env bash
# ==============================================================================
# LibraFlow — Hardware Virtualization Capability Check Script
# Purpose: Verifies whether the Linux host CPU supports hardware virtualization
#          (Intel VT-x or AMD SVM) and checks KVM module readiness.
# ==============================================================================

set -euo pipefail

echo "=============================================================="
echo " LibraFlow Virtualization Diagnostic Utility"
echo "=============================================================="

# 1. Check OS Kernel
OS_NAME=$(uname -s)
if [[ "${OS_NAME}" != "Linux" ]]; then
    echo "[!] Warning: This script is intended for Linux environments."
    echo "    Current OS detected: ${OS_NAME}."
    echo "    On Windows, please run VirtualBox or enable Hyper-V/WSL2."
    exit 1
fi

echo "[*] Operating System: Linux ($(uname -r))"

# 2. Check for CPU Virtualization Flags
VIRT_FLAG_COUNT=$(grep -E -c '(vmx|svm)' /proc/cpuinfo || true)

if [[ "${VIRT_FLAG_COUNT}" -gt 0 ]]; then
    # Identify CPU architecture
    if grep -q 'vmx' /proc/cpuinfo; then
        CPU_VENDOR="Intel (VT-x supported)"
    else
        CPU_VENDOR="AMD (AMD-V / SVM supported)"
    fi
    echo "[+] Hardware Virtualization Flag: ENABLED (${CPU_VENDOR}, ${VIRT_FLAG_COUNT} vCPUs)"
else
    echo "[-] Hardware Virtualization Flag: NOT DETECTED"
    echo "    Ensure 'Intel Virtualization Technology' or 'SVM' is enabled in your BIOS/UEFI settings."
    echo "    If running inside a VM (nested virtualization), enable nested VT-x/AMD-V in hypervisor settings."
    exit 2
fi

# 3. Check for kvm-ok command (cpu-checker package)
if command -v kvm-ok &>/dev/null; then
    echo "[*] Running kvm-ok validation:"
    kvm-ok || true
else
    echo "[i] Tip: Install 'cpu-checker' package ('sudo apt install cpu-checker') for extended diagnostic checks."
fi

# 4. Check /dev/kvm character device
if [[ -e /dev/kvm ]]; then
    echo "[+] /dev/kvm Device: PRESENT"
    if [[ -r /dev/kvm && -w /dev/kvm ]]; then
        echo "[+] /dev/kvm Permissions: READ/WRITE accessible by current user."
    else
        echo "[!] /dev/kvm Permissions: Restricted. Current user ($(whoami)) may need membership in 'kvm' group."
        echo "    Run: sudo usermod -aG kvm $(whoami)"
    fi
else
    echo "[-] /dev/kvm Device: NOT PRESENT"
    echo "    KVM kernel modules may not be loaded."
    echo "    Attempt loading modules with: sudo modprobe kvm"
    if grep -q 'vmx' /proc/cpuinfo; then
        echo "    For Intel CPUs: sudo modprobe kvm_intel"
    else
        echo "    For AMD CPUs: sudo modprobe kvm_amd"
    fi
    exit 3
fi

echo "=============================================================="
echo "[+] SUCCESS: Host environment is fully capable of running KVM/QEMU virtualization!"
echo "=============================================================="
exit 0
