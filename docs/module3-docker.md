# Module 3 — Containerization Using Docker

This guide documents the containerization of **LibraFlow — Library Management System** using Docker and Docker Compose. It is designed for BCA students to demonstrate container technology during practical lab evaluations and viva voce examinations.

---

## 1. Core Container Concepts Explained

### 1.1 Docker Image vs Docker Container
* **Docker Image**: An immutable, read-only template that contains the application source code, runtime (Python 3.12), system libraries, dependencies, and configuration. It is built from a `Dockerfile`.
* **Docker Container**: A runnable, isolated instance of a Docker image. It includes a thin read-write layer on top of the image layers where runtime operations occur.

### 1.2 Port Mapping (`-p 5000:5000`)
Containers run in their own isolated network namespace. Port mapping forwards traffic from a port on the host machine (e.g. Windows localhost `5000`) to a listening port inside the container (`5000`).
```
[Host Browser: http://localhost:5000]
                 │
                 ▼ Port Forwarding (-p 5000:5000)
    [Container Network: Gunicorn listening on 0.0.0.0:5000]
```

### 1.3 Volume Persistence (`-v libraflow-db-data:/app/data`)
Because container file systems are ephemeral by default (data written inside a container is lost when the container is deleted), a **named volume** is mounted to `/app/data`. The SQLite database (`libraflow.db`) is written to this volume, ensuring that book loans, returns, and member records persist across container restarts and updates.

### 1.4 Environment Variables (`-e`)
Configuration settings (such as `SECRET_KEY`, `FLASK_ENV`, `LOAN_PERIOD_DAYS`) are injected at runtime into the container without hardcoding sensitive values into image layers.

### 1.5 Production WSGI Server (Gunicorn)
Flask's built-in development server is single-threaded and not designed for production concurrency or security. LibraFlow runs under **Gunicorn** (`Green Unicorn`), a production WSGI HTTP server with multiple worker processes and threads:
```
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 "app:app"
```

---

## 2. Step-by-Step Hands-On Commands (PowerShell)

### Step 2.1 Verify Docker Installation
Open PowerShell in the project directory:
```powershell
docker --version
docker compose version
```
*Expected Output:*
```
Docker version 27.x.x (or 29.x.x)
Docker Compose version v2.x.x
```

---

### Step 2.2 Build the Docker Image
Build the image with a local tag `libraflow-app:1.0.0`:
```powershell
docker build -t libraflow-app:1.0.0 .
```
*Explanation:*
* `-t libraflow-app:1.0.0`: Specifies the image name and version tag.
* `.`: Context directory (Docker sends the files in current directory, excluding files in `.dockerignore`).

---

### Step 2.3 Run the Container with Port Mapping and Volume
Run the container in detached mode (`-d`) with a custom name:
```powershell
docker run -d `
  --name libraflow-container `
  -p 5000:5000 `
  -e SECRET_KEY="prod-super-secret-key-libraflow-2026" `
  -e FLASK_ENV="production" `
  -v libraflow-db-data:/app/data `
  libraflow-app:1.0.0
```

---

### Step 2.4 Verify Container Status and Health Check
List running containers:
```powershell
docker ps
```
*Expected Output:*
```
CONTAINER ID   IMAGE                  STATUS                   PORTS                    NAMES
a1b2c3d4e5f6   libraflow-app:1.0.0    Up 25 seconds (healthy)  0.0.0.0:5000->5000/tcp   libraflow-container
```

Test the health check endpoint from PowerShell:
```powershell
Invoke-RestMethod -Uri http://localhost:5000/health
```
*Expected JSON Output:*
```json
{
  "database": "healthy",
  "service": "LibraFlow Library Management System",
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-10-17T06:00:40.791891Z"
}
```

---

### Step 2.5 Inspect Container Logs
Stream real-time Gunicorn application access and error logs:
```powershell
docker logs -f libraflow-container
```
Press `Ctrl + C` to exit log streaming.

---

### Step 2.6 Container Lifecycle Management
To pause, stop, restart, or remove the container:
```powershell
# Stop container
docker stop libraflow-container

# Start stopped container
docker start libraflow-container

# Restart container
docker restart libraflow-container

# Force-remove container (data in named volume remains safe)
docker rm -f libraflow-container
```

---

### Step 2.7 Orchestration with Docker Compose
Instead of long command-line options, Docker Compose simplifies multi-step lifecycle management:

```powershell
# Build and start container in background
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f

# Shut down container
docker compose down
```

---

## 3. Publishing to Docker Hub (Image Registry)

To share the image or prepare it for Kubernetes deployment:

### Step 3.1 Authenticate with Docker Hub
```powershell
docker login
```
Enter your Docker Hub username and password/token when prompted.

### Step 3.2 Tag the Image with Your Registry Namespace
Replace `<YOUR_DOCKERHUB_USERNAME>` with your actual Docker Hub username:
```powershell
$DOCKER_USER = "yourusername"
docker tag libraflow-app:1.0.0 ${DOCKER_USER}/libraflow:1.0.0
docker tag libraflow-app:1.0.0 ${DOCKER_USER}/libraflow:latest
```

### Step 3.3 Push to Docker Hub
```powershell
docker push ${DOCKER_USER}/libraflow:1.0.0
docker push ${DOCKER_USER}/libraflow:latest
```

### Step 3.4 Pull and Run on Any Target Machine
Anyone (or a Kubernetes cluster) can run your published image:
```powershell
docker run -d -p 5000:5000 ${DOCKER_USER}/libraflow:1.0.0
```

---

## 4. Troubleshooting Common Docker Issues

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `port is already allocated: 5000` | Another local process (e.g. AirPlay, local Flask app) is listening on port 5000. | Stop the local app or map to a different host port: `-p 5050:5000`. |
| `container exited with code 1` | Database permission error or missing environment variable. | Check logs using `docker logs libraflow-container`. |
| `Health status: unhealthy` | The `/health` endpoint failed or timed out during the initial 10s start period. | Verify that Gunicorn is bound to `0.0.0.0:5000` (not `127.0.0.1`). |
