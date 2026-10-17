#!/usr/bin/env bash
# ==============================================================================
# LibraFlow — KVM, QEMU & Libvirt Automated Setup Script
# Purpose: Installs KVM hypervisor packages, libvirt daemons, bridge networking,
#          and Virt-Manager graphical UI on Debian/Ubuntu systems.
# ==============================================================================

set -euo pipefail

echo "=============================================================="
echo " LibraFlow KVM & Libvirt Automated Installation Utility"
echo "=============================================================="

# Ensure running with root / sudo privileges
if [[ "${EUID}" -ne 0 ]]; then
    echo "[-] Error: Please execute this setup script with sudo privileges:"
    echo "    sudo $0"
    exit 1
fi

TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo '')}"
if [[ -z "${TARGET_USER}" || "${TARGET_USER}" == "root" ]]; then
    TARGET_USER="${1:-}"
    if [[ -z "${TARGET_USER}" ]]; then
        echo "[!] Warning: Could not detect standard non-root username."
        echo "    Usage: sudo $0 <username>"
        exit 1
    fi
fi

echo "[*] Updating apt package repository lists..."
apt update -y

echo "[*] Installing KVM, QEMU, Libvirt, and Virt-Manager..."
apt install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virt-manager \
    virtinst \
    cpu-checker

echo "[*] Enabling and starting the libvirtd background daemon..."
systemctl enable --now libvirtd.service

echo "[*] Adding user '${TARGET_USER}' to 'libvirt' and 'kvm' security groups..."
usermod -aG libvirt "${TARGET_USER}"
usermod -aG kvm "${TARGET_USER}"

echo "[*] Verifying libvirt daemon status..."
if systemctl is-active --quiet libvirtd; then
    echo "[+] libvirtd service is ACTIVE and running."
else
    echo "[-] Warning: libvirtd service failed to start. Run: sudo systemctl status libvirtd"
fi

echo "=============================================================="
echo "[+] KVM/QEMU installation completed successfully!"
echo "    IMPORTANT: User '${TARGET_USER}' must log out and log back in"
echo "    (or reboot) for group permissions to take full effect."
echo "    Launch graphical manager with: virt-manager"
echo "=============================================================="
