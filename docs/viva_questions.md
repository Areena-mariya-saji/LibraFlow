# LibraFlow — Comprehensive Viva Voce Questions & Answers

This guide prepares BCA students for practical lab exams, project demonstrations, and oral viva questions covering the full stack and all five syllabus modules.

---

## Section 1: Full-Stack Web Application & Database

### Q1: What is LibraFlow and what problem does it solve?
**Answer:** LibraFlow is a full-stack library management system designed to automate library operations, including book cataloging, unique accession tracking for physical copies, member borrowing lifecycles, reservation hold queues, and automatic overdue fine calculations.

### Q2: Why did you choose SQLite for this project?
**Answer:** SQLite is a lightweight, serverless, zero-configuration relational database stored in a single cross-platform file. It is ideal for local development, reproducible automated testing, and college microproject demonstrations without requiring complex database server setup.

### Q3: How does LibraFlow enforce copy-level tracking?
**Answer:** While a title record exists once in the `books` table, each individual physical copy in the library is given its own record in the `book_copies` table with a unique accession number (e.g. `LIB-CC-001`), shelf location, and status (`available`, `borrowed`, `reserved`, `maintenance`). This prevents duplicate loans for the same physical book.

### Q4: How is password security implemented?
**Answer:** Passwords are never stored in plain text. We use Werkzeug’s cryptographic password hashing functions (`generate_password_hash` and `check_password_hash`) utilizing salted scrypt or bcrypt hashes.

### Q5: What is CSRF protection and how is it handled?
**Answer:** Cross-Site Request Forgery (CSRF) is an attack where an unauthorized site tricks an authenticated user into executing unwanted actions. LibraFlow generates a unique cryptographic 24-byte hex token in each session, verifies it on every incoming POST request, and rejects invalid requests with HTTP 400.

### Q6: How does the system calculate overdue fines?
**Answer:** When loans are checked, the system calculates days late using the difference between the current date and the `due_date`. For each day overdue, a penalty is computed based on `FINE_PER_DAY` and synchronized into the `fines` table.

---

## Section 2: Module 1 — Introduction to Virtualization

### Q7: What is virtualization?
**Answer:** Virtualization is a technology that allows multiple operating systems to run concurrently on a single physical computer by partitioning physical hardware into virtual machines using a hypervisor.

### Q8: What is the difference between a Type 1 and Type 2 hypervisor?
**Answer:**
* **Type 1 (Bare-Metal)**: Runs directly on physical hardware without a host OS (e.g., VMware ESXi, KVM). Used in data centers and cloud platforms.
* **Type 2 (Hosted)**: Runs as an application inside a host operating system (e.g., VirtualBox, VMware Workstation). Used on developer desktops.

### Q9: What is the difference between Host OS and Guest OS?
**Answer:** The Host OS is the operating system installed directly on the physical hardware (e.g., Windows 11). The Guest OS is the operating system running inside a virtual machine (e.g., Ubuntu Linux).

### Q10: What is a VM snapshot and why is it useful?
**Answer:** A snapshot captures the complete state of a virtual machine (virtual disk, RAM, and configuration) at a specific point in time. It provides instant disaster recovery: if an update or configuration fails, the VM can be reverted to the snapshot within seconds.

---

## Section 3: Module 2 — Virtualization Tools and Automation

### Q11: What is KVM and how does it differ from QEMU?
**Answer:** KVM (Kernel-based Virtual Machine) is a Linux kernel module that provides kernel-level CPU virtualization. QEMU provides hardware emulation (motherboard, network cards, disk controllers). Together, KVM provides near-native execution speed while QEMU handles virtual device emulation.

### Q12: How do you verify if a CPU supports hardware virtualization on Linux?
**Answer:** By checking for the `vmx` (Intel) or `svm` (AMD) CPU flags in `/proc/cpuinfo`, or by executing the `kvm-ok` command from the `cpu-checker` package.

### Q13: What is `libvirt` and `virsh`?
**Answer:** `libvirt` is an open-source management library and daemon (`libvirtd`) providing a uniform API for hypervisors. `virsh` is the command-line management tool used to script, automate, start, stop, and inspect virtual machines.

---

## Section 4: Module 3 — Containerization Using Docker

### Q14: What is the difference between a Docker image and a Docker container?
**Answer:** A Docker image is a read-only, immutable package containing application code, runtime, libraries, and dependencies. A Docker container is an active, runnable instance of an image with an ephemeral writable layer.

### Q15: Why use Gunicorn instead of the Flask development server in Docker?
**Answer:** Flask's built-in development server is single-threaded, unoptimized for high concurrency, and insecure for production. Gunicorn is a battle-tested WSGI HTTP server with multi-process worker pools that handle concurrent user requests safely.

### Q16: Why are Docker volumes necessary for database storage?
**Answer:** Container file systems are ephemeral; any data written inside a container is erased when the container is deleted or recreated. A Docker volume stores data outside the container lifecycle on the host machine, ensuring database persistence.

### Q17: What does port mapping `-p 5000:5000` do?
**Answer:** It binds port 5000 on the host machine to port 5000 inside the container network namespace, allowing external traffic (such as a web browser) to reach the application.

---

## Section 5: Module 4 — Kubernetes Orchestration

### Q18: What is a Pod in Kubernetes?
**Answer:** A Pod is the smallest deployable execution unit in Kubernetes. It encapsulates one or more containers that share the same network namespace (IP address) and storage volumes.

### Q19: What is the purpose of a Kubernetes Deployment?
**Answer:** A Deployment declaratively manages ReplicaSets, enabling automated zero-downtime rolling updates, scaling, health self-healing, and rollbacks.

### Q20: What is the difference between Liveness and Readiness probes?
**Answer:**
* **Liveness Probe**: Determines if the container is healthy. If it fails, Kubernetes kills and restarts the Pod.
* **Readiness Probe**: Determines if the container is ready to accept user network traffic. If it fails, the Pod is temporarily removed from the Service's traffic routing.

### Q21: What happens if you scale a Pod using an internal SQLite database?
**Answer:** Each Pod will maintain its own isolated, separate SQLite file. Writes in one Pod will not be visible in others. For multi-replica scaling in production, applications must connect to a centralized external database like PostgreSQL or MySQL.

---

## Section 6: Module 5 — Serverless Architecture (AWS Lambda)

### Q22: What is Function-as-a-Service (FaaS)?
**Answer:** FaaS is a cloud computing model where developers upload discrete event-driven functions (like AWS Lambda). The cloud provider automatically provisions infrastructure, scales on demand, and charges only for the exact milliseconds of execution.

### Q23: What role does Amazon API Gateway play?
**Answer:** API Gateway acts as the public entry point (front door) for serverless backends. It accepts incoming HTTP requests from users and routes them to the appropriate AWS Lambda function.

### Q24: How does S3 event notification work?
**Answer:** When an object is created or modified in an S3 bucket (e.g. `s3:ObjectCreated:Put`), S3 publishes an event containing object metadata to AWS Lambda, triggering an event-processing function.

### Q25: What is a cold start in AWS Lambda?
**Answer:** A cold start is the brief latency (~100-300ms) that occurs when a Lambda function is invoked after being idle, during which AWS spins up a new container sandbox and initializes the runtime.
