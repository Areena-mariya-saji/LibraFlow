# Module 4 — Container Orchestration with Kubernetes

This guide documents the orchestration of **LibraFlow** using Kubernetes and Minikube on Windows. It fulfills the Module 4 syllabus requirements for the BCA microproject evaluation and viva voce.

---

## 1. Kubernetes Architecture & Concepts Explained

### 1.1 Pod, ReplicaSet, and Deployment Hierarchy
```
                   [Deployment: libraflow-deployment]
                    Controls rollout strategy, revisions
                                  │
                                  ▼
                   [ReplicaSet: libraflow-xxxxxxxxxx]
                    Maintains desired number of Pod copies
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
       [Pod: Replica 1]    [Pod: Replica 2]    [Pod: Replica 3]
       IP: 10.244.0.5      IP: 10.244.0.6      IP: 10.244.0.7
```

* **Pod**: The smallest deployable computing unit in Kubernetes. A Pod encapsulates one or more containers, shared storage volumes, and a unique network IP.
* **ReplicaSet**: Ensures that a specified number of Pod replicas are running at any given time.
* **Deployment**: A higher-level abstraction that declaratively manages ReplicaSets, enabling zero-downtime rolling updates, rollbacks, and pause/resume capabilities.

### 1.2 Probes (Health & Readiness)
* **Liveness Probe**: Checks if the container is alive. If `GET /health` fails repeatedly, kubelet kills and restarts the container.
* **Readiness Probe**: Checks if the container is ready to accept user traffic. If `GET /health` fails, the Pod's IP is removed from the Service endpoints until it recovers.

### 1.3 Service Types
* **ClusterIP** (Default): Exposes the service on a cluster-internal IP. Accessible only from within the Kubernetes cluster.
* **NodePort**: Exposes the service on each Node’s IP at a static port (in the range `30000-32767`, e.g., `30080`). Allows external client access.

### 1.4 Database Considerations & SQLite in Distributed Pods
> [!IMPORTANT]
> **Database Architecture Reality**:
> SQLite is an in-process, single-file database. When running multiple Pod replicas, each Pod receives an isolated, independent file copy. Writes performed in Pod A are **not** replicated to Pod B or Pod C.
>
> * **For Simple Single-Node Demonstration**: 1 Pod replica is deployed with local SQLite persistence.
> * **For Horizontal Scaling Demonstration**: Multiple replicas are scaled up to demonstrate Kubernetes replica management, but in production this requires an external centralized database such as AWS RDS PostgreSQL or MySQL.

---

## 2. Setting Up Minikube on Windows

### Step 2.1 Verify Prerequisites
Ensure Docker Desktop is running, then check `kubectl` and `minikube`:
```powershell
kubectl version --client
minikube version
```

### Step 2.2 Start Minikube with the Docker Driver
```powershell
minikube start --driver=docker --cpus=2 --memory=3072
```
*Expected Output:*
```
* Starting "minikube" primary components in control plane node
* Running on "docker" driver with 2 CPUs and 3072MiB of memory
* Done! kubectl is now configured to use "minikube" cluster
```

### Step 2.3 Load the Local Docker Image into Minikube
Because Minikube runs inside its own isolated Docker engine, load the local `libraflow-app:1.0.0` image directly into Minikube without needing to push to Docker Hub:
```powershell
minikube image load libraflow-app:1.0.0
```
Verify the image exists inside Minikube:
```powershell
minikube image list | Select-String "libraflow"
```

---

## 3. Deploying LibraFlow to Kubernetes

### Step 3.1 Create the Namespace
```powershell
kubectl apply -f kubernetes/namespace.yaml
```
Verify:
```powershell
kubectl get namespaces
```

### Step 3.2 Create the Secret
Create `secret.yaml` from the example template and apply it:
```powershell
Copy-Item kubernetes/secret.yaml.example kubernetes/secret.yaml
kubectl apply -f kubernetes/secret.yaml
```

### Step 3.3 Create the ConfigMap
```powershell
kubectl apply -f kubernetes/configmap.yaml
```

### Step 3.4 Deploy the Application and NodePort Service
```powershell
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

---

## 4. Inspecting and Accessing the Application

### Step 4.1 Check Pod Status and Logs
List all resources in the `libraflow` namespace:
```powershell
kubectl get all -n libraflow
```
*Expected Output:*
```
NAME                                       READY   STATUS    RESTARTS   AGE
pod/libraflow-deployment-xxxxxxxxxx-xxxxx  1/1     Running   0          45s

NAME                         TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/libraflow-service    NodePort   10.108.120.45   <none>        80:30080/TCP   45s

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/libraflow-deployment   1/1     1            1           45s
```

View real-time application logs from the running Pod:
```powershell
kubectl logs -f deployment/libraflow-deployment -n libraflow
```

Inspect detailed Pod conditions, events, and health probe checks:
```powershell
kubectl describe pod -l app=libraflow -n libraflow
```

---

### Step 4.2 Method A: Access via Port Forwarding
Port forward local host port `8080` to the Pod's port `5000`:
```powershell
kubectl port-forward service/libraflow-service 8080:80 -n libraflow
```
Open your browser and navigate to:
`http://localhost:8080`

Test the health probe through port-forward:
```powershell
Invoke-RestMethod -Uri http://localhost:8080/health
```

---

### Step 4.3 Method B: Access via Minikube NodePort Tunnel
In a separate PowerShell window:
```powershell
minikube service libraflow-service -n libraflow --url
```
This generates a direct browser URL (e.g. `http://127.0.0.1:xxxxx`) routed through the Minikube networking proxy.

---

## 5. Scaling and Horizontal Demonstration

### Step 5.1 Scale Replicas to 3
```powershell
kubectl scale deployment/libraflow-deployment --replicas=3 -n libraflow
```

### Step 5.2 Observe New Pods Creation
```powershell
kubectl get pods -n libraflow -w
```
*Expected Output:*
```
NAME                                    READY   STATUS    RESTARTS   AGE
libraflow-deployment-xxxxxxxxxx-aaa11   1/1     Running   0          2m
libraflow-deployment-xxxxxxxxxx-bbb22   1/1     Running   0          10s
libraflow-deployment-xxxxxxxxxx-ccc33   1/1     Running   0          10s
```

### Step 5.3 Scale Back to 1 Replica
```powershell
kubectl scale deployment/libraflow-deployment --replicas=1 -n libraflow
```

---

## 6. Rolling Updates and Rollback Demonstration

### Step 6.1 Trigger a Rolling Update
Update the container image to version `1.1.0` (or your Docker Hub tag):
```powershell
kubectl set image deployment/libraflow-deployment libraflow-web=libraflow-app:1.1.0 -n libraflow
```

### Step 6.2 Monitor Rollout Progress
```powershell
kubectl rollout status deployment/libraflow-deployment -n libraflow
```
Kubernetes starts new Pods with the new version and only terminates old Pods after the readiness probe passes (`maxUnavailable: 0`).

### Step 6.3 Rollback to Previous Stable Version
If an update causes errors, perform an instant zero-downtime rollback:
```powershell
# View rollout revision history
kubectl rollout history deployment/libraflow-deployment -n libraflow

# Undo rollout back to the previous working revision
kubectl rollout undo deployment/libraflow-deployment -n libraflow

# Confirm rollback completion
kubectl rollout status deployment/libraflow-deployment -n libraflow
```

---

## 7. Troubleshooting Kubernetes Deployments

| Error State | Typical Cause | Resolution Command |
| :--- | :--- | :--- |
| `ErrImagePull` / `ImagePullBackOff` | Image name is misspelled or not loaded into Minikube. | Run `minikube image load libraflow-app:1.0.0` or verify Docker Hub repository. |
| `CrashLoopBackOff` | Application crashed inside container or database permission issue. | Check logs: `kubectl logs -l app=libraflow -n libraflow --previous`. |
| `0/1 nodes available` | Insufficient CPU or memory allocated to Minikube. | Reduce resource requests in `deployment.yaml` or restart Minikube with more RAM. |
| Pod stuck in `Pending` | Secret or ConfigMap missing. | Run `kubectl describe pod <pod-name> -n libraflow` and verify `libraflow-secret` exists. |
