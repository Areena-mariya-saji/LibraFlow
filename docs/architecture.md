# LibraFlow — System Architecture & Deployment Blueprint

This document details the architectural design of **LibraFlow — Library Management System**, spanning core application layers, containerized deployment pipelines, Kubernetes cluster orchestration, and AWS serverless extensions.

> [!NOTE]
> **Complementary Deployment Stages**:
> Virtualization, Docker, Kubernetes, and Serverless represent progressive deployment tiers of the modern software lifecycle rather than a mandate to execute every component simultaneously. Each module demonstrates practical mastery of specific cloud-native infrastructure competencies.

---

## 1. Core Application Architecture

The monolithic web application is constructed around a clean Model-View-Controller (MVC) paradigm:

```mermaid
flowchart TD
    subgraph ClientLayer["User Access Layer (Browser)"]
        Member["Library Member (Student)"]
        Admin["Administrator"]
    end

    subgraph PresentationLayer["Presentation Layer (Bootstrap 5 & Custom CSS)"]
        Views["Jinja2 HTML Templates\n(Catalogs, Loans, Fines, Dashboards)"]
        Static["Static Assets (CSS, JS, Icons)"]
    end

    subgraph AppLayer["Application Core (Python Flask & Gunicorn)"]
        Router["Flask URL Routing & Blueprints"]
        Auth["Session Management & CSRF Guard"]
        BusinessLogic["Circulation & Reservation Engine"]
        OverdueCron["Overdue & Fine Calculation Service"]
    end

    subgraph DataLayer["Persistence Layer (SQLite Database)"]
        DB[("SQLite3 Database\n(libraflow.db)\nForeign Keys Enabled")]
    end

    Member --> Views
    Admin --> Views
    Views --> Router
    Router --> Auth
    Auth --> BusinessLogic
    BusinessLogic --> DB
    OverdueCron --> DB
```

---

## 2. Containerization & Registry Pipeline (Docker & Docker Hub)

```mermaid
flowchart LR
    Dev["Developer Workstation\n(Source Code)"] -->|"git commit & push"| Git["GitHub Repository"]
    Dev -->|"docker build -t"| Img["Docker Image\n(Python 3.12 + Gunicorn)"]
    Img -->|"docker push"| Reg["Docker Hub Registry\n(yourusername/libraflow:1.0.0)"]
    Reg -->|"docker pull"| Staging["Staging / Production Host"]
    Staging -->|"docker run with volume"| Container["Running Container\n(Port 5000:5000)"]
    Container --> Vol[("Named Volume\n(libraflow-db-data)")]
```

---

## 3. Kubernetes Orchestration Architecture (Minikube / Production Cluster)

```mermaid
flowchart TD
    Client["External User / Browser"] -->|"HTTP Port 30080"| NodePort["Kubernetes Service (NodePort: 30080)"]
    
    subgraph Cluster["Kubernetes Cluster (libraflow namespace)"]
        NodePort -->|"TargetPort 5000"| Deploy["Deployment: libraflow-deployment\n(Strategy: RollingUpdate)"]
        
        Deploy --> RS["ReplicaSet (Active Revision)"]
        
        subgraph Pods["Pod Replicas"]
            P1["Pod 1: libraflow-web\nCPU: 100m, RAM: 128Mi\nProbes: Liveness & Readiness"]
        end
        
        RS --> P1
        
        CM["ConfigMap: libraflow-config\n(PORT, FLASK_ENV, FINE_PER_DAY)"] -.->|Inject Env| P1
        Sec["Secret: libraflow-secret\n(SECRET_KEY)"] -.->|Inject Env| P1
    end
```

---

## 4. Serverless Event-Driven Microservices (AWS Lambda & API Gateway)

```mermaid
flowchart LR
    subgraph ClientAccess["Client Requests"]
        ClientApp["Student / Mobile Client"]
        S3Uploader["Admin Catalog Export"]
    end

    subgraph AWSCloud["AWS Serverless Architecture"]
        APIGW["Amazon API Gateway\n(/books/availability & /books/reserve)"]
        LambdaA["AWS Lambda: BookAvailabilityFunction\n(JSON Inventory Metrics)"]
        LambdaB["AWS Lambda: BookReservationFunction\n(Validation & Token Issuance)"]
        
        S3Bucket[("Amazon S3 Bucket\n(libraflow-catalog-bucket)")]
        LambdaC["AWS Lambda: S3EventProcessorFunction\n(Sanitized Metadata Logger)"]
        CloudWatch["Amazon CloudWatch Logs"]
    end

    ClientApp -->|"GET /books/availability"| APIGW
    APIGW --> LambdaA
    ClientApp -->|"POST /books/reserve"| APIGW
    APIGW --> LambdaB

    S3Uploader -->|"s3:ObjectCreated:Put"| S3Bucket
    S3Bucket --> LambdaC
    LambdaC --> CloudWatch
```

---

## 5. Architectural Comparison Matrix

| Attribute | Virtual Machine (VirtualBox/KVM) | Container (Docker) | Orchestration (Kubernetes) | Serverless (AWS Lambda) |
| :--- | :--- | :--- | :--- | :--- |
| **Virtualization Level** | Hardware-level (Hypervisor) | OS-level (Kernel namespaces) | Cluster-level (Nodes & Pods) | Function-level (Runtime sandbox) |
| **Boot Latency** | Minutes (~30s - 2m) | Seconds (~1s - 3s) | Seconds (~2s - 5s) | Milliseconds (~100ms cold start) |
| **Resource Efficiency** | High memory overhead (guest OS kernel) | Lightweight (shares host kernel) | Highly optimized resource bin-packing | Zero idle consumption |
| **State Management** | Persistent virtual disk (VDI/QCOW2) | Persistent via Named Volumes | PVC / PersistentVolumes | Stateless (external DynamoDB/RDS) |
| **Scaling Model** | Manual VM provisioning | Manual or script-driven (`docker compose up --scale`) | Automated Horizontal Pod Autoscaling (HPA) | Automatic concurrency (0 to thousands) |
