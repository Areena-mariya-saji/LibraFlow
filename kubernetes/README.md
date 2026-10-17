# LibraFlow — Kubernetes Deployment Manifests

This directory contains the Kubernetes manifests required to deploy **LibraFlow** on a local Minikube cluster or managed cloud Kubernetes service (EKS/GKE/AKS).

## Manifest Files Summary

| File | Resource Kind | Purpose |
| :--- | :--- | :--- |
| `namespace.yaml` | `Namespace` | Creates isolated `libraflow` cluster namespace. |
| `configmap.yaml` | `ConfigMap` | Stores non-sensitive application settings (`PORT`, `LOAN_PERIOD_DAYS`, etc.). |
| `secret.yaml.example` | `Secret` | Template for base64-encoded `SECRET_KEY`. |
| `deployment.yaml` | `Deployment` | Manages Pod replicas, CPU/memory limits, rolling updates, and liveness/readiness probes. |
| `service.yaml` | `Service` | Exposes the application using NodePort `30080` (or internal ClusterIP). |

## Quick Apply Order

```powershell
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Copy and apply secret
Copy-Item secret.yaml.example secret.yaml
kubectl apply -f secret.yaml

# 3. Apply ConfigMap
kubectl apply -f configmap.yaml

# 4. Apply Deployment & Service
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 5. Verify deployment
kubectl get all -n libraflow
```

For complete step-by-step instructions with scaling, rolling updates, rollbacks, and Minikube commands, refer to [docs/module4-kubernetes.md](../docs/module4-kubernetes.md).
