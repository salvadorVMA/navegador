# Azure VM & Docker Deployment: SSH and Container Registry Setup Guide

This document summarizes the steps taken to set up SSH keys for secure access (both on the host and inside the container), configure, log in, and push Docker images to Azure Container Registry (ACR), and set up a robust remote development environment on your Azure VM with XFCE desktop, VS Code desktop, and persistent GitHub authentication.

---

## 1. SSH Key Setup (Host & Container)

### 1.1. Generate SSH Key Pair (if not already present)
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# or for RSA (if needed):
# ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```
- Save to: `~/.ssh/azure_vm_key` (or your preferred name)
- Do NOT set a passphrase for automated use (optional, but recommended for automation).

### 1.2. Add Public Key to Azure VM
- Copy the public key to the VM:
```bash
ssh-copy-id -i ~/.ssh/azure_vm_key.pub <azureuser>@<vm-ip>
```
- Or manually append the contents of `~/.ssh/azure_vm_key.pub` to `~/.ssh/authorized_keys` on the VM.

### 1.3. Configure SSH on Host
- Edit `~/.ssh/config`:
```
Host azure-vm
    HostName <vm-ip>
    User <azureuser>
    IdentityFile ~/.ssh/azure_vm_key
    IdentitiesOnly yes
```
- Test connection:
```bash
ssh azure-vm
```

### 1.4. Add SSH Key to SSH Agent (for scripts)
```bash
ssh-add ~/.ssh/azure_vm_key
```

### 1.5. (Optional) Copy SSH Key into Docker Container
- Add to Dockerfile:
```
COPY .ssh/azure_vm_key /root/.ssh/id_ed25519
COPY .ssh/azure_vm_key.pub /root/.ssh/id_ed25519.pub
RUN chmod 600 /root/.ssh/id_ed25519 && chmod 644 /root/.ssh/id_ed25519.pub
```
- Or mount at runtime:
```bash
docker run -v ~/.ssh:/root/.ssh ...
```

---

## 2. Azure Container Registry (ACR) Setup & Docker Push

### 2.1. Check if Docker is Installed
```bash
docker --version || echo "Docker is not installed. Please install Docker before proceeding."
```

### 2.2. Install Azure CLI (if not present)
```bash
brew update && brew install azure-cli
```

### 2.3. Log in to Azure
```bash
az login
```

### 2.4. Log in to Azure Container Registry
```bash
az acr login --name <acr-name>
# Example: az acr login --name navegador1acr
```

### 2.5. Tag Docker Image for ACR
```bash
docker tag navegador-dashboard:latest <acr-name>.azurecr.io/navegador-dashboard:latest
# Example: docker tag navegador-dashboard:latest navegador1acr.azurecr.io/navegador-dashboard:latest
```

### 2.6. Push Docker Image to ACR
```bash
docker push <acr-name>.azurecr.io/navegador-dashboard:latest
# Example: docker push navegador1acr.azurecr.io/navegador-dashboard:latest
```

---

## 3. Troubleshooting
- If you see `authentication required` or `insufficient_scope` errors, ensure you are logged in to both Azure and ACR.
- If SSH fails, check permissions on private keys (`chmod 600`), and that the public key is in `~/.ssh/authorized_keys` on the VM.
- For automated scripts, always ensure the SSH key is loaded in the agent (`ssh-add`).

---

## 4. References
- [Azure CLI Install Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Container Registry Docs](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Docker Push Docs](https://docs.docker.com/engine/reference/commandline/push/)
- [SSH Key Docs](https://www.ssh.com/academy/ssh/keygen)

---

## 5. VM Sizing and Desktop Environment Setup

### 5.1. VM Sizing
- For remote desktop and VS Code desktop, use at least Standard B2s (2 vCPUs, 4 GiB RAM) or higher. Smaller VMs (e.g., B1s) will freeze or be unresponsive with desktop workloads.

### 5.2. Install XFCE Desktop Environment
```bash
sudo apt update
sudo apt install -y xfce4 xfce4-goodies
```

### 5.3. Install xrdp for Remote Desktop Access
```bash
sudo apt install -y xrdp
sudo systemctl enable xrdp
sudo systemctl start xrdp
echo "startxfce4" > ~/.xsession
```

### 5.4. Open Firewall for RDP (Port 3389)
- In Azure portal, add an inbound rule for TCP port 3389 to your VM's network security group.
- Optionally, enable UFW and allow 3389:
```bash
sudo ufw allow 3389/tcp
```

### 5.5. Set a Password for RDP Login
```bash
sudo passwd azureuser
```
Use this password for RDP login (SSH keys are not used for RDP).

### 5.6. Connect via Microsoft Remote Desktop (Windows/macOS) or Remmina (Linux)
- Use your VM's public IP and username/password.

### 5.7. Install VS Code Desktop
```bash
wget -qO- https://update.code.visualstudio.com/latest/linux-deb-x64/stable | sudo dpkg -i
# If the above fails:
wget https://update.code.visualstudio.com/latest/linux-deb-x64/stable -O vscode.deb
sudo apt install ./vscode.deb
```

---

## 6. Persistent GitHub Authentication in VS Code Desktop

### 6.1. Install Keyring Packages
```bash
sudo apt update
sudo apt install gnome-keyring libsecret-1-0
```

### 6.2. Add Keyring to XFCE Session Startup
- Go to XFCE "Settings" → "Session and Startup" → "Application Autostart".
- Add:
  - Name: GNOME Keyring
  - Command: /usr/bin/gnome-keyring-daemon --start --components=secrets

### 6.3. Log Out and Log Back In
- This ensures the keyring daemon starts with your session.

### 6.4. Verify Keyring is Running
```bash
ps aux | grep keyring
```

### 6.5. Sign In to GitHub in VS Code
- Use device code authentication and copy the link/code to your local browser if the VM browser is slow.
- Credentials should now persist across VS Code restarts.

---

## 7. VS Code Server (code-server) for Lightweight Remote Development

- For resource-constrained environments, use code-server for browser-based VS Code sessions.
- Most extensions (except Copilot) work; ideal for Python, Jupyter, Git, Docker, and data analysis workflows.
- Use separate user-data-dirs and ports for parallel, isolated sessions.
- Automate setup with scripts for reproducibility.

---

## 8. General Best Practices
- Always use SSH keys for secure, automated access.
- Use device code authentication for GitHub sign-in if browser is slow.
- Resize VM as needed for desktop workloads.
- Use keyring for persistent credentials.
- Prefer code-server for lightweight, browser-based development when desktop is not required.
