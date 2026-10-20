# LibraFlow — Practical Record Screenshots Checklist

This document provides a structured guide for capturing and organizing screenshots for your practical record, lab file, and presentation slides.

> [!NOTE]
> In accordance with academic honesty guidelines, do not fabricate or alter screenshots. Capture real screenshots directly from your running environment using the Windows Snipping Tool (`Win + Shift + S`) or Ubuntu Screenshot utility.

---

## 1. Web Application & Functional Modules

| Filename | View / Page | Key Elements to Capture |
| :--- | :--- | :--- |
| `01_homepage.png` | Homepage (`/`) | Hero section, search bar, inventory metric counters (Total Titles, Physical Copies, Available Copies), and featured books grid. |
| `02_login_demo_pills.png` | Sign In Page (`/login`) | Login form showing the one-click credential buttons (`Admin`, `Student 1`). |
| `03_admin_dashboard.png` | Admin Dashboard (`/admin/dashboard`) | KPI stat cards, Recent Loan Transactions table, and Recent Users panel. |
| `04_circulation_desk.png` | Circulation & Loans (`/loans`) | Loan ledger, one-click return actions, and book issuance desk modal. |
| `05_student_dashboard.png` | Student Dashboard (`/member/dashboard`) | Current borrowed books, active due date warnings, reservation status, and outstanding fines. |
| `06_catalog_search_filters.png` | Books Catalog (`/books`) | Filtered search results showing category pill tags and copy availability badges (`Available Now` vs `All Borrowed`). |
| `07_book_detail_accessions.png` | Book Details (`/books/<id>`) | Bibliographic details, Reserve button, and table of physical copies with unique accession numbers (`LIB-CC-001`, `LIB-CC-002`). |
| `08_loan_issue_modal.png` | Issue Book Modal (`/loans`) | Member selector and available copy dropdown with 14-day loan notice. |
| `09_return_fines_ledger.png` | Fines Ledger (`/fines`) | Overdue loan penalties table with "Mark as Paid" and "Waive" administrative desk actions. |
| `10_inventory_reports.png` | Reports & Audit (`/reports`) | Category distribution breakdown table and overdue loans audit list. |

---

## 2. Automated Testing Suite

| Filename | Test Action | Key Elements to Capture |
| :--- | :--- | :--- |
| `11_pytest_all_passed.png` | Terminal running `pytest -v` | Green test output showing 23 passed unit tests in `~2.7s` across authentication, books, circulation, and health checks. |

---

## 3. Module 1: Virtualization (VirtualBox)

| Filename | Virtualization Step | Key Elements to Capture |
| :--- | :--- | :--- |
| `12_virtualbox_vm_specs.png` | VirtualBox Manager | VM settings dialog displaying 4096 MB RAM, 2 vCPUs, and 25 GB VDI disk. |
| `13_virtualbox_port_forward.png` | Network Settings | Port forwarding rule mapping Host Port 5000 to Guest Port 5000. |
| `14_virtualbox_app_running.png` | Host Browser + VM Window | Split screen showing LibraFlow loaded at `http://localhost:5000` in Windows with Ubuntu terminal running Gunicorn/Flask. |
| `15_virtualbox_snapshot.png` | Snapshots Panel | Snapshot tree showing `LibraFlow-Working-Baseline`. |

---

## 4. Module 2: KVM & Shell Automation

| Filename | Command / Tool | Key Elements to Capture |
| :--- | :--- | :--- |
| `16_check_virtualization.png` | `scripts/check_virtualization.sh` | Terminal output displaying CPU flags (`vmx`/`svm`), `/dev/kvm` presence, and `[+] SUCCESS` diagnostic. |
| `17_manage_vm_script.png` | `scripts/manage_vm.sh list` | Output of `virsh list --all` showing defined KVM domains. |

---

## 5. Module 3: Docker Containerization

| Filename | Docker Action | Key Elements to Capture |
| :--- | :--- | :--- |
| `18_docker_build.png` | `docker build -t libraflow-app:1.0.0 .` | Terminal showing multi-stage image build and layer caching. |
| `19_docker_ps_healthy.png` | `docker ps` | Running container showing `Up (healthy)` status and port mapping `0.0.0.0:5000->5000/tcp`. |
| `20_docker_health_curl.png` | `Invoke-RestMethod http://localhost:5000/health` | JSON response confirming healthy status. |
| `21_docker_compose_up.png` | `docker compose up -d` | Compose orchestrating web container and persistent named volume. |

---

## 6. Module 4: Kubernetes (Minikube)

| Filename | Kubernetes Command | Key Elements to Capture |
| :--- | :--- | :--- |
| `22_kubectl_get_all.png` | `kubectl get all -n libraflow` | Running Pod, NodePort Service (`30080`), and Deployment in `libraflow` namespace. |
| `23_kubectl_scale_3_pods.png` | `kubectl get pods -n libraflow` | 3 running Pod replicas after `kubectl scale --replicas=3`. |
| `24_kubectl_rolling_update.png` | `kubectl rollout status ...` | Successful zero-downtime rolling update output. |
| `25_kubectl_rollout_undo.png` | `kubectl rollout undo ...` | Rollback confirmation message. |

---

## 7. Module 5: AWS Serverless

| Filename | Serverless Execution | Key Elements to Capture |
| :--- | :--- | :--- |
| `26_serverless_local_tests.png` | `python serverless/test_local.py` | Terminal output confirming all 3 Lambda functions (Availability GET, Reservation POST, S3 Event trigger) passed local verification. |
| `27_sam_template_validate.png` | `sam validate` (Optional) | Successful SAM CloudFormation template validation. |
