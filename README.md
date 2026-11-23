# Anas Patel Final Project - Simple To-Do App

A small to-do app built with Python and FastAPI for IT-390.

## Features

- List tasks
- Filter tasks by All / Open / Done
- Add a task
- Mark a task complete, or click its green "Done" label to move it back to To-Do
- Delete a task
- JSON API at `/api/tasks`
- Health check at `/health`

Tasks are kept in memory, so they reset when the app restarts.

## Prerequisites

Install these before following the steps below:

| Tool | Needed for | Check with |
|------|------------|------------|
| Git | Cloning the repo | `git --version` |
| Python 3.12+ | Running the app and tests locally | `python3 --version` |
| Docker Desktop | Docker and Compose steps | `docker --version` and `docker compose version` |
| kubectl | Kubernetes steps | `kubectl version --client` |
| kind | Local Kubernetes cluster | `kind version` |

Clone the repository first:

```bash
git clone https://github.com/depaul-teaching/Anas-Final.git
cd Anas-Final
```

## Run locally

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000.

Run the tests:

```bash
pytest
```

## Run with Docker

Build the image:

```bash
docker build -t task-tracker:dev .
```

Run it:

```bash
docker run --rm -p 8000:8000 -e ENVIRONMENT=docker -e APP_TITLE="Anas Task Tracker" task-tracker:dev
```

Open http://localhost:8000. Check health with `curl -i http://localhost:8000/health`.

## Run with Docker Compose

Start the whole stack (app + Nginx) with one command:

```bash
docker compose up --build
```

Open http://localhost:8080. Nginx listens on port 8080 and forwards requests to the app. The app container has no published port, so it is only reachable through Nginx.

Check health through the proxy:

```bash
curl -i http://localhost:8080/health
```

Stop and remove the containers:

```bash
docker compose down
```

| Service | Image | Purpose |
|---------|-------|---------|
| `app`   | built from `Dockerfile` | The FastAPI task tracker |
| `nginx` | `nginx:1.27-alpine` | Reverse proxy in front of the app |

Nginx finds the app through environment variables set in `compose.yaml`, so no host or port is hard-coded in the config:

| Variable   | Value  | What it does                                 |
|------------|--------|----------------------------------------------|
| `APP_HOST` | `app`  | Compose service name of the app              |
| `APP_PORT` | `8000` | Port the app listens on inside its container |

The app's own variables can be overridden from your shell:

```bash
ENVIRONMENT=staging docker compose up --build
```

## CI/CD (GitHub Actions)

The workflow is in `.github/workflows/ci.yml`.

**Triggers:** every push to `main` and every pull request.

| Job       | Runs when                                 | What it does |
|-----------|-------------------------------------------|--------------|
| `tests`   | push to `main`, any PR                    | Installs the pinned dependencies and runs `pytest` |
| `publish` | push to `main` only, after `tests` passes | Builds the Docker image for `linux/amd64` and `linux/arm64` and pushes it to GHCR |

The image is published to GitHub Container Registry, tagged with the first 7 characters of the commit SHA:

```
ghcr.io/depaul-teaching/anas-final:sha-<commit>
```

The package is public, so it can be pulled without logging in:

```bash
docker pull ghcr.io/depaul-teaching/anas-final:sha-<commit>
```

The workflow stops at publishing the image. It does not deploy to Kubernetes, which is done manually with `kubectl` (see below). It uses the built-in `GITHUB_TOKEN`, so no secrets are stored in the repository.

## Run on Kubernetes (kind)

Requires `kubectl` and a running kind cluster. Check that the cluster is reachable:

```bash
kubectl config current-context
kubectl get nodes
```

Apply all the manifests in `k8s/`:

```bash
kubectl apply -f k8s/
kubectl get pods
```

Wait until both the `app` and `nginx` pods show `1/1 Running`, then forward a local port to Nginx:

```bash
kubectl port-forward svc/nginx 8082:80
```

In a second terminal:

```bash
curl -i http://localhost:8082/health
```

Open http://localhost:8082. The banner says `Environment: kubernetes`.

| File | What it creates |
|------|-----------------|
| `k8s/app-deployment.yaml` | App pods, using the GHCR image pinned by its `sha-` tag, with env vars and a readiness probe on `/health` |
| `k8s/app-service.yaml` | Internal Service named `app` on port 8000 |
| `k8s/nginx-configmap.yaml` | Nginx config template with `${APP_HOST}` and `${APP_PORT}` placeholders |
| `k8s/nginx-deployment.yaml` | Nginx pod that mounts the ConfigMap and gets `APP_HOST` and `APP_PORT` from `env:` |
| `k8s/nginx-service.yaml` | Internal Service named `nginx` on port 80 |

Nginx reaches the app by its Service name (`app`), the same way Compose does. To deploy a new build, change the `sha-` tag in `k8s/app-deployment.yaml` to the one CI published, then run `kubectl apply -f k8s/` again.

### Operations

```bash
kubectl scale deployment app --replicas=3            # scale up
kubectl scale deployment app --replicas=1            # scale down
kubectl delete pod -l app=app                        # the Deployment replaces the pod
kubectl set env deployment/app ENVIRONMENT=staging   # rolling update
kubectl rollout status deployment/app
kubectl rollout undo deployment/app                  # roll back
kubectl describe pod <pod-name>                      # events and probe failures
kubectl logs <pod-name>                              # container logs
```

Tasks are stored in memory, so with more than one replica each pod keeps its own list.

## Architecture

```
 Developer
    |  git push
    v
 GitHub repo (main)
    |  triggers
    v
 GitHub Actions
    1. tests    -> pytest
    2. publish  -> docker buildx (amd64 + arm64)
    |
    v
 GHCR  ghcr.io/depaul-teaching/anas-final:sha-<commit>
    |
    |  kubectl apply -f k8s/   (manual, not part of CI)
    v
 kind cluster
 +---------------------------------------------------------------+
 |  Service nginx :80                                            |
 |      |                                                        |
 |      v                                                        |
 |  Deployment nginx  <-- ConfigMap nginx-template (mounted)     |
 |      |  env: APP_HOST=app, APP_PORT=8000                      |
 |      v                                                        |
 |  Service app :8000                                            |
 |      |                                                        |
 |      v                                                        |
 |  Deployment app  (GHCR image, readiness probe on /health)     |
 +---------------------------------------------------------------+
    ^
    |  kubectl port-forward svc/nginx 8082:80
 Browser
```

The Compose stack follows the same shape: a browser reaches Nginx on port 8080, and Nginx forwards to the `app` service on the Compose network.

## Architecture notes

**Why this setup**

- **Nginx in front of the app.** It is the single entry point, so the app itself is never published to the host. It is a small supporting service that is easy to explain.
- **Environment variables for the upstream.** Nginx reads `APP_HOST` and `APP_PORT` from its environment, so no host or port is hard-coded. The same config template works in Compose and in Kubernetes.
- **Images pinned by `sha-` tag.** The Deployment never uses `latest`, so every running pod can be traced to one commit and a rollback goes back to a known build.
- **Multi-architecture image.** CI builds for `amd64` (GitHub runners) and `arm64` (Apple Silicon laptops and the kind node).
- **Pipeline stops at publishing.** Deployment is done by hand with `kubectl`, which keeps the pipeline simple and makes each Kubernetes step visible.

**Tradeoffs**

- **In-memory data.** Tasks reset when a pod restarts, and each replica keeps its own list. This kept the app small, and it shows how containers and state interact.
- **ConfigMap for the Nginx config.** It avoids building a second custom image, but the config now lives in a Kubernetes object as well as in the repo.
- **`port-forward` instead of Ingress.** It is enough to reach the app from a laptop on kind, and it avoids extra moving parts.
- **Single replica by default.** Deleting the pod causes a short gap, and more replicas would remove it at the cost of separate task lists.
- **Slower publish job.** Building the arm64 image under emulation adds a few minutes to each run.

## Problems and fixes

**1. Image would not pull on an Apple Silicon Mac.**
`docker pull` failed with `no matching manifest for linux/arm64/v8`. GitHub's runner is `amd64`, so CI had published an amd64-only image. I worked around it once by pulling the amd64 digest, then fixed the cause by adding `docker/setup-qemu-action`, `docker/setup-buildx-action` and `platforms: linux/amd64,linux/arm64` to the publish job. A plain pull then worked.

**2. Container exited right after starting.**
Two typos in the Dockerfile `CMD`. `sh: 1: PORT: not found` meant the variable was written as `$(PORT)` instead of `${PORT}`. After that, `Import string "app.main.app" must be in format "<module>:<attribute>"` meant a dot where the colon belongs. The fix was `app.main:app`.

**3. Troubleshooting exercise: wrong upstream port.**
To practice diagnosis, I set `APP_PORT=9999` on the Nginx Deployment. The new pod stayed `0/1` while the old pod kept serving, because a rolling update waits for the readiness probe. `kubectl describe pod` showed `APP_PORT: 9999` and `Readiness probe failed ... context deadline exceeded`. `kubectl logs` showed `GET /health` returning `499` from `kube-probe`, meaning Nginx was waiting on an upstream that never answered. `kubectl rollout undo deployment/nginx` restored `APP_PORT: 8000`, and `/health` answered through Nginx again.

## Environment variables

| Variable      | Default             | What it does                          |
|---------------|---------------------|---------------------------------------|
| `APP_TITLE`   | `Anas's To-Do List` | Browser tab title                     |
| `ENVIRONMENT` | `local`             | Shown in the banner at the top        |

Example:

```bash
APP_TITLE="My Tasks" ENVIRONMENT=staging uvicorn app.main:app
```

## Endpoints

| Method | Path                         | Description                                    |
|--------|------------------------------|------------------------------------------------|
| GET    | `/`                          | Home page (`?status=all\|open\|done`)          |
| POST   | `/tasks`                     | Add a task (HTML form)                         |
| POST   | `/tasks/{id}/complete`       | Mark a task complete (HTML form)               |
| POST   | `/tasks/{id}/reopen`         | Move a task back to To-Do (HTML form)          |
| POST   | `/tasks/{id}/delete`         | Delete a task (HTML form)                      |
| GET    | `/api/tasks`                 | List tasks as JSON (`?status=all\|open\|done`) |
| POST   | `/api/tasks`                 | Add a task, body: `{"title": "..."}`           |
| POST   | `/api/tasks/{id}/complete`   | Mark a task complete                           |
| POST   | `/api/tasks/{id}/reopen`     | Move a task back to To-Do                      |
| DELETE | `/api/tasks/{id}`            | Delete a task                                  |
| GET    | `/health`                    | Returns `{"status": "ok"}`                     |