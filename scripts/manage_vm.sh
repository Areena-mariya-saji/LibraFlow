#!/usr/bin/env bash
# ==============================================================================
# LibraFlow — KVM Virtual Machine Automation Script
# Purpose: Provides command-line lifecycle management for KVM/libvirt VMs
#          (start, stop, reboot, status, list, info, console).
# ==============================================================================

set -euo pipefail

function show_usage() {
    cat << EOF
Usage: $0 <COMMAND> [VM_NAME]

Commands:
  list                List all defined virtual machines and their current state
  status  <VM_NAME>   Show detailed power status of the specified VM
  start   <VM_NAME>   Power on / boot the specified VM
  stop    <VM_NAME>   Gracefully shut down the specified VM (ACPI shutdown)
  force-stop <VM_NAME> Immediately terminate / power off the specified VM
  reboot  <VM_NAME>   Gracefully reboot the specified VM
  info    <VM_NAME>   Display vCPU, memory, and XML domain metadata
  console <VM_NAME>   Connect to text serial console (Escape with Ctrl + ])

Examples:
  $0 list
  $0 start libraflow-vm
  $0 status libraflow-vm
  $0 stop libraflow-vm
EOF
}

# Require virsh command
if ! command -v virsh &>/dev/null; then
    echo "[-] Error: 'virsh' command not found."
    echo "    Please install libvirt tools: sudo apt install libvirt-clients"
    exit 1
fi

COMMAND="${1:-}"
VM_NAME="${2:-}"

if [[ -z "${COMMAND}" ]]; then
    show_usage
    exit 1
fi

case "${COMMAND}" in
    list)
        echo "[*] Listing all KVM Virtual Machines:"
        virsh list --all
        ;;

    status)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 status libraflow-vm"
            exit 1
        fi
        echo "[*] Status for Virtual Machine '${VM_NAME}':"
        virsh domstate "${VM_NAME}" || {
            echo "[-] Virtual machine '${VM_NAME}' not found."
            exit 2
        }
        ;;

    start)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 start libraflow-vm"
            exit 1
        fi
        echo "[*] Booting Virtual Machine '${VM_NAME}'..."
        virsh start "${VM_NAME}"
        echo "[+] VM '${VM_NAME}' started successfully."
        ;;

    stop)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 stop libraflow-vm"
            exit 1
        fi
        echo "[*] Sending graceful ACPI shutdown signal to '${VM_NAME}'..."
        virsh shutdown "${VM_NAME}"
        echo "[+] Shutdown signal dispatched. VM is shutting down."
        ;;

    force-stop)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 force-stop libraflow-vm"
            exit 1
        fi
        echo "[!] Forcefully terminating '${VM_NAME}' (destroy domain)..."
        virsh destroy "${VM_NAME}"
        echo "[+] VM '${VM_NAME}' powered off."
        ;;

    reboot)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 reboot libraflow-vm"
            exit 1
        fi
        echo "[*] Rebooting Virtual Machine '${VM_NAME}'..."
        virsh reboot "${VM_NAME}"
        echo "[+] Reboot initiated."
        ;;

    info)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 info libraflow-vm"
            exit 1
        fi
        echo "[*] Domain Information for '${VM_NAME}':"
        virsh dominfo "${VM_NAME}"
        ;;

    console)
        if [[ -z "${VM_NAME}" ]]; then
            echo "[-] Error: Please specify the VM name. Example: $0 console libraflow-vm"
            exit 1
        fi
        echo "[*] Connecting to serial console of '${VM_NAME}' (Press 'Ctrl + ]' to exit):"
        virsh console "${VM_NAME}"
        ;;

    *)
        echo "[-] Unknown command: '${COMMAND}'"
        show_usage
        exit 1
        ;;
esac
