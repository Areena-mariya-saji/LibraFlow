# Module 1 — Introduction to Virtualization

This laboratory guide covers the fundamentals of hardware virtualization, hypervisor classifications, and running **LibraFlow — Library Management System** inside an Ubuntu Linux Virtual Machine using Oracle VM VirtualBox.

---

## 1. Virtualization Fundamentals & Architecture

### 1.1 Type 1 vs Type 2 Hypervisors

```
      [Type 1 Hypervisor / Bare Metal]             [Type 2 Hypervisor / Hosted]
 ┌───────────────────────────────────────┐   ┌───────────────────────────────────────┐
 │ VM 1 (Ubuntu) │ VM 2 (Windows Server) │   │ VM 1 (Ubuntu) │ VM 2 (Debian)         │
 ├───────────────────────────────────────┤   ├───────────────────────────────────────┤
 │     Hypervisor (ESXi / KVM / Xen)     │   │ Hypervisor (VirtualBox / VMware Work) │
 ├───────────────────────────────────────┤   ├───────────────────────────────────────┤
 │         Physical Bare-Metal Hardware  │   │       Host OS (Windows 11 / macOS)    │
 └───────────────────────────────────────┘   ├───────────────────────────────────────┤
                                             │         Physical Hardware (CPU/RAM)   │
                                             └───────────────────────────────────────┘
```

| Characteristic | Type 1 Hypervisor (Bare-Metal) | Type 2 Hypervisor (Hosted) |
| :--- | :--- | :--- |
| **Architecture** | Runs directly on the physical computer hardware without an underlying OS. | Runs as an application inside a Host Operating System (e.g. Windows 11). |
| **Performance** | High performance, negligible latency, near native hardware speeds. | Slight overhead because I/O passes through the host OS kernel. |
| **Examples** | VMware ESXi, Proxmox VE, Microsoft Hyper-V (Core), KVM. | Oracle VM VirtualBox, VMware Workstation Pro, VMware Fusion. |
| **Primary Use** | Enterprise data centers, cloud infrastructure (AWS EC2, Azure). | Developer workstations, desktop testing, academic laboratories. |

### 1.2 Core Terminology Explained
* **Host Operating System**: The primary OS installed directly on the physical machine (e.g., Windows 11).
* **Guest Operating System**: The secondary OS installed and running inside the virtual machine (e.g., Ubuntu 24.04 LTS).
* **Hypervisor (VMM - Virtual Machine Monitor)**: Software that virtualizes hardware resources (CPU, RAM, Storage, NIC) and mediates access between guest machines and physical hardware.
* **Virtual Hardware**: Emulated components presented to the guest OS (vCPU, vRAM, virtual IDE/SATA disk controller, virtual Intel PRO/1000 network card).

### 1.3 How Virtualization Supports Application Deployment
1. **Environment Isolation**: LibraFlow dependencies (Python packages, system libraries) run in complete isolation from the host OS, preventing conflicts with other software.
2. **Reproducibility**: Development and production environments can be replicated identically across machines.
3. **Disaster Recovery**: Instant snapshotting allows rolling back a corrupted state within seconds.

---

## 2. Step-by-Step Practical Lab: Setting Up LibraFlow on Ubuntu VM

### Step 2.1 Download and Install Oracle VM VirtualBox
1. Download **VirtualBox 7.x** from [virtualbox.org](https://www.virtualbox.org/).
2. Run the Windows installer (`VirtualBox-7.x.x-Win.exe`) with default features.
3. Install the **VirtualBox Extension Pack** for USB 3.0 and RDP support.
4. Download the **Ubuntu 24.04 LTS Desktop/Server ISO** from [ubuntu.com](https://ubuntu.com/download/desktop).

---

### Step 2.2 Create and Configure the Ubuntu Virtual Machine
1. Open VirtualBox and click **New**.
2. Configure basic parameters:
   * **Name**: `LibraFlow-Ubuntu-VM`
   * **Type**: `Linux`
   * **Version**: `Ubuntu (64-bit)`
   * **ISO Image**: Select the downloaded `ubuntu-24.04-desktop-amd64.iso`.
3. Configure Hardware:
   * **Base Memory (RAM)**: `4096 MB` (4 GB recommended; minimum 2048 MB).
   * **Processors (vCPU)**: `2 CPUs` (ensure processor execution cap is 100%).
4. Configure Virtual Hard Disk:
   * **Disk Size**: `25.00 GB` (Dynamically Allocated VDI - VirtualBox Disk Image).
5. Click **Finish**.

> **[Screenshot Placeholder 1.1: VirtualBox VM Hardware Configuration Window showing 4GB RAM and 2 vCPUs]**

---

### Step 2.3 Network Configuration (Port Forwarding)
To access LibraFlow running inside the VM from your Windows host browser:
1. In VirtualBox, select `LibraFlow-Ubuntu-VM` and click **Settings** > **Network**.
2. Set **Adapter 1** to **NAT**.
3. Expand **Advanced** and click **Port Forwarding**.
4. Add a new rule:
   * **Name**: `LibraFlow-Web`
   * **Protocol**: `TCP`
   * **Host IP**: `127.0.0.1`
   * **Host Port**: `5000`
   * **Guest IP**: Leave blank (or enter guest IP e.g. `10.0.2.15`)
   * **Guest Port**: `5000`
5. Click **OK**.

> **[Screenshot Placeholder 1.2: VirtualBox NAT Port Forwarding dialog showing Host 5000 mapped to Guest 5000]**

---

### Step 2.4 Installing Ubuntu OS & Guest Additions
1. Start the VM and complete the standard Ubuntu installation wizard.
2. Create your administrative user account (e.g., `student` / `Password123`).
3. After rebooting into Ubuntu, open a terminal (`Ctrl + Alt + T`) and update packages:
```bash
sudo apt update && sudo apt upgrade -y
```
4. Install VirtualBox Guest Additions for shared clipboard and display auto-resize:
```bash
sudo apt install -y build-essential dkms linux-headers-$(uname -r)
```

---

### Step 2.5 Deploying and Running LibraFlow Inside Ubuntu
1. Install Python 3, `pip`, and virtual environment tools:
```bash
sudo apt install -y python3 python3-pip python3-venv git
```

2. Clone or copy the project files into the Ubuntu home directory:
```bash
cd ~
git clone https://github.com/<your-username>/libraflow.git
cd libraflow
```

3. Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install requirements:
```bash
pip install -r requirements.txt
```

5. Initialize and seed the library database:
```bash
python3 database/seed_data.py
```

6. Launch LibraFlow:
```bash
python3 app.py
```
*Expected Output:*
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

7. Open your Windows Host browser and navigate to:
```
http://localhost:5000
```
LibraFlow is now serving web traffic from inside the Ubuntu virtual machine to your Windows host!

> **[Screenshot Placeholder 1.3: LibraFlow dashboard loaded in Windows browser while running inside the Ubuntu VirtualBox window]**

---

## 3. Snapshot Management (Disaster Recovery Demonstration)

Snapshots preserve the exact state of a virtual machine's virtual disk, RAM, and hardware configuration at a specific point in time.

### 3.1 Taking a Snapshot
1. In the VirtualBox main window, select `LibraFlow-Ubuntu-VM` and click the **Snapshots** tab (or press `Ctrl + Shift + S`).
2. Click **Take**.
3. Name: `LibraFlow-Working-Baseline`.
4. Description: `Clean installation of Ubuntu 24.04 with Python 3, seeded SQLite database, and passing test suite.`
5. Click **OK**.

> **[Screenshot Placeholder 1.4: VirtualBox Snapshots panel showing 'LibraFlow-Working-Baseline']**

### 3.2 Simulating Failure and Restoring Snapshot
To demonstrate recovery during viva evaluation:
1. Inside Ubuntu terminal, intentionally damage a file:
```bash
rm database/libraflow.db
```
2. Try visiting `http://localhost:5000` — the database error confirms failure.
3. Shut down the VM.
4. In VirtualBox Snapshots panel, select `LibraFlow-Working-Baseline` and click **Restore**.
5. Start the VM again. Notice that `database/libraflow.db` is completely restored to working order!

---

## 4. Cloning Virtual Machines

VirtualBox allows creating clones for horizontal testing:
* **Full Clone**: An independent duplicate copy of the virtual disk image. Consumes separate disk space.
* **Linked Clone**: A snapshot-dependent copy that references the parent virtual disk, saving disk space.

Command to clone via CLI (`VBoxManage`):
```powershell
VBoxManage clonevm "LibraFlow-Ubuntu-VM" --name "LibraFlow-Clone-Node2" --register --mode all
```

---

## 5. Troubleshooting VirtualBox Common Issues

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `VT-x/AMD-V hardware acceleration is not available` | CPU virtualization (Intel VT-x or AMD-SVM) is disabled in the PC BIOS/UEFI. | Reboot PC, enter BIOS setup, enable "Intel Virtualization Technology" or "SVM Mode". |
| `Failed to open a session for the virtual machine (VERR_SUP_VP_FEEDBACK_REQUIRED)` | Windows Hyper-V conflict or Device Guard enabled. | Disable Memory Integrity in Windows Core Isolation or run VirtualBox as Administrator. |
| `Unable to connect from Host Browser` | Port forwarding rule missing or bound to guest `127.0.0.1` instead of `0.0.0.0`. | Verify `app.run(host="0.0.0.0", port=5000)` in `app.py`. |
