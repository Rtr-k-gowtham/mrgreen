# 🚀 VPS Auto-Deployment Guide

MR.GREEN is configured with **continuous deployment** via GitHub Actions. Every time you push changes to `main`, GitHub Actions connects to your VPS over SSH and updates the application automatically.

---

## 📋 One-Time VPS Setup

### Step 1: Install Docker & Git on your VPS
SSH into your VPS and run:
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Git and Curl
sudo apt install -y git curl

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Allow current user to run Docker without sudo (optional but recommended)
sudo usermod -aG docker $USER
```
*(Log out and log back in for docker group permissions to take effect).*

---

### Step 2: Clone MR.GREEN onto your VPS
Choose a target folder (for example `/opt/mrgreen` or `~/mrgreen`):
```bash
# Create directory and take ownership
sudo mkdir -p /opt/mrgreen
sudo chown -R $USER:$USER /opt/mrgreen

# Clone the repo
git clone https://github.com/Rtr-k-gowtham/mrgreen.git /opt/mrgreen
cd /opt/mrgreen

# Make deploy script executable
chmod +x scripts/deploy.sh
```

---

### Step 3: Configure `.env` on your VPS
Inside `/opt/mrgreen`:
```bash
cp backend/.env.example .env
nano .env
```
Ensure your configuration points to your database and Ollama instance. If Ollama runs directly on the VPS host:
```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

### Step 4: Run Initial Deployment
Run the deployment script once manually to verify everything builds and starts:
```bash
bash scripts/deploy.sh
```
Check health:
```bash
curl http://localhost:8000/health
```

---

## 🔑 Configure GitHub Repository Secrets

To enable GitHub Actions to SSH into your VPS on push:

1. Open your GitHub repository: [Rtr-k-gowtham/mrgreen](https://github.com/Rtr-k-gowtham/mrgreen)
2. Go to **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** and add the following 4 secrets:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `VPS_HOST` | VPS public IP or domain name | `123.45.67.89` |
| `VPS_USER` | SSH user | `root` or `ubuntu` |
| `VPS_SSH_KEY` | Private SSH key (`id_ed25519` or `id_rsa`) | `-----BEGIN OPENSSH PRIVATE KEY----- ...` |
| `VPS_PATH` | Path where repo is cloned on VPS | `/opt/mrgreen` |
| `VPS_PORT` *(Optional)* | SSH port (defaults to 22) | `22` |

> [!TIP]
> If you need to generate a dedicated SSH key pair on your VPS for GitHub Actions:
> ```bash
> ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions -N ""
> cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
> chmod 600 ~/.ssh/authorized_keys
> cat ~/.ssh/github_actions
> ```
> Copy the output of `cat ~/.ssh/github_actions` and paste it as `VPS_SSH_KEY` in GitHub Secrets.

---

## 🔄 How it Works
From now on:
```bash
git add .
git commit -m "update feature"
git push
```
GitHub Actions will automatically trigger, connect to your VPS, pull the changes, rebuild any modified containers, and verify that the API is healthy!
