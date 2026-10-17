# Module 2 — Virtualization Tools and Automation

This guide covers advanced enterprise virtualization using **KVM (Kernel-based Virtual Machine)**, **QEMU**, **libvirt**, and shell script automation. It fulfills the Module 2 syllabus requirements for the BCA microproject evaluation.

---

## 1. Enterprise Linux Virtualization Architecture

### 1.1 KVM, QEMU, and Libvirt Stack
```
┌────────────────────────────────────────────────────────┐
│   Management Tools (virsh CLI / Virt-Manager GUI)      │
├────────────────────────────────────────────────────────┤
│   libvirt API & Daemon (libvirtd)                      │
├────────────────────────────────────────────────────────┤
│   QEMU (Hardware Emulation, I/O devices, virtio)       │
├────────────────────────────────────────────────────────┤
│   KVM Kernel Module (kvm.ko, kvm_intel.ko / kvm_amd.ko)│
├────────────────────────────────────────────────────────┤
│   Linux Kernel & Hardware (Intel VT-x / AMD SVM)       │
└────────────────────────────────────────────────────────┘
```

* **KVM (Kernel-based Virtual Machine)**: A Linux kernel module that turns the host Linux kernel into a Type 1 hypervisor. It enables direct access to CPU virtualization extensions.
* **QEMU (Quick Emulator)**: Provides user-space virtual hardware emulation (PC motherboard, disk controllers, NIC, VGA). When paired with KVM, QEMU uses KVM for CPU execution, achieving near bare-metal performance.
* **Libvirt**: An open-source API, daemon (`libvirtd`), and management tool suite that provides a stable, uniform abstraction layer over KVM/QEMU.
* **Virsh**: The primary command-line interface for scripting and automating virtual machine domains.
* **Virt-Manager**: A desktop GUI application for managing KVM virtual machines.

### 1.2 Windows vs Linux Virtualization Notice
> [!IMPORTANT]
> **Host Environment Notice**:
> KVM is built directly into the Linux kernel and cannot run natively on standard Windows. 
> To practice KVM automation:
> 1. Run inside your Ubuntu VirtualBox VM with **Nested Virtualization** enabled (`Enable Nested VT-x/AMD-V` in VirtualBox CPU settings).
> 2. Or boot into a Linux live USB or dual-boot setup.

---

## 2. Checking Hardware Virtualization Support

Before creating KVM guests, verify that your CPU supports hardware-assisted virtualization.

### Step 2.1 Run the Automated Diagnostic Script
Execute the provided script:
```bash
bash scripts/check_virtualization.sh
```

### Step 2.2 Manual Verification Commands
Inspect CPU flags:
```bash
# Check count of hardware virtualization threads (should be > 0)
egrep -c '(vmx|svm)' /proc/cpuinfo

# Check KVM compatibility tool
sudo apt install -y cpu-checker
kvm-ok
```
*Expected Output:*
```
INFO: /dev/kvm exists
KVM acceleration can be used
```

Verify `/dev/kvm` character device permissions:
```bash
ls -l /dev/kvm
```
*Expected Output:*
```
crw-rw----+ 1 root kvm 10, 232 Oct 17 06:15 /dev/kvm
```

---

## 3. Automated KVM & Libvirt Setup

### Step 3.1 Run the Setup Script
Run the installation automation script:
```bash
chmod +x scripts/*.sh
sudo ./scripts/setup_kvm.sh
```

This script:
1. Updates package repositories.
2. Installs `qemu-kvm`, `libvirt-daemon-system`, `libvirt-clients`, `bridge-utils`, and `virt-manager`.
3. Enables and starts the `libvirtd` systemd service.
4. Adds your user account to the `libvirt` and `kvm` groups.

---

## 4. Virtual Machine Lifecycle Automation (`virsh` & `manage_vm.sh`)

We provide `scripts/manage_vm.sh` to automate VM management without memorizing long commands:

### 4.1 List All Defined Virtual Machines
```bash
./scripts/manage_vm.sh list
```
*Output:*
```
[*] Listing all KVM Virtual Machines:
 Id   Name           State
------------------------------
 1    libraflow-vm   running
 -    ubuntu-node2   shut off
```

### 4.2 Start / Boot a Virtual Machine
```bash
./scripts/manage_vm.sh start libraflow-vm
```

### 4.3 Check VM Status
```bash
./scripts/manage_vm.sh status libraflow-vm
```
*Output:*
```
[*] Status for Virtual Machine 'libraflow-vm':
running
```

### 4.4 Inspect Detailed Domain Info
```bash
./scripts/manage_vm.sh info libraflow-vm
```
*Output:*
```
Id:             1
Name:           libraflow-vm
OS Type:        hvm
State:          running
CPU(s):         2
Max memory:     4194304 KiB
Used memory:    4194304 KiB
```

### 4.5 Graceful Shutdown & Force Stop
```bash
# Send ACPI shutdown signal
./scripts/manage_vm.sh stop libraflow-vm

# In case of emergency or hung guest:
./scripts/manage_vm.sh force-stop libraflow-vm
```

---

## 5. Provisioning a KVM Guest via CLI (`virt-install`)

To create a new headless Ubuntu server VM completely through the command line:

```bash
sudo virt-install \
  --name libraflow-vm \
  --ram 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/libraflow-vm.qcow2,size=20,format=qcow2 \
  --os-variant ubuntu22.04 \
  --network network=default \
  --graphics none \
  --console pty,target_type=serial \
  --location 'http://archive.ubuntu.com/ubuntu/dists/noble/main/installer-amd64/' \
  --extra-args 'console=ttyS0,115200n8 serial'
```

---

## 6. Troubleshooting Common KVM / Libvirt Errors

| Error | Root Cause | Resolution |
| :--- | :--- | :--- |
| `permission denied on /dev/kvm` | User is not in the `kvm` group or has not re-logged in. | Run `sudo usermod -aG kvm $(whoami)` then log out and log back in. |
| `failed to connect to socket '/var/run/libvirt/libvirt-sock'` | The `libvirtd` daemon is stopped. | Run `sudo systemctl start libvirtd`. |
| `KVM acceleration can NOT be used` | Nested virtualization is disabled in the parent hypervisor. | In Windows PowerShell, run: `VBoxManage modifyvm "<VM_NAME>" --nested-hw-virt on`. |
