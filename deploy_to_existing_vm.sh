#!/bin/bash
# Script to deploy Docker container to existing Azure VM

set -e  # Exit immediately if a command exits with non-zero status

echo "===== Navegador Azure VM Deployment (Existing VM) ====="
echo

# Hardcoded configuration variables
RESOURCE_GROUP="navegador-rg"
VM_NAME="navegador-vm"
ADMIN_USERNAME="azureuser"
DOCKER_IMAGE_NAME="navegador-dashboard"
DOCKER_IMAGE_TAG="latest"
VM_IP="40.76.249.194"  # Hardcoded VM IP address

echo "Using hardcoded configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  VM Name: $VM_NAME"
echo "  Admin Username: $ADMIN_USERNAME"
echo "  Docker Image: $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG"
echo "  VM IP address: $VM_IP"

echo
echo "=== Building Docker Image ==="
echo "Building $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG..."

# Check if environment_working.yml exists in the current directory or needs to be copied
if [ ! -f "environment_working.yml" ] && [ -f "config/environment_working.yml" ]; then
    echo "Copying environment_working.yml from config directory..."
    cp config/environment_working.yml .
fi

echo "Building for linux/amd64 platform to ensure compatibility with Azure VMs..."
# Always use buildx for cross-platform builds
if ! docker buildx version > /dev/null 2>&1; then
    echo "ERROR: Docker BuildX is required for cross-platform builds. Please install Docker BuildX."
    exit 1
fi
docker buildx create --name navegador-builder || true
docker buildx use navegador-builder
docker buildx build --platform linux/amd64 --load -t "$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG" .

echo
echo "=== Saving Docker Image ==="
echo "Saving image to $DOCKER_IMAGE_NAME.tar..."
docker save -o "$DOCKER_IMAGE_NAME.tar" "$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG"

echo
echo "=== Checking SSH Key Access ==="
# Using hardcoded SSH key path with proper expansion
SSH_KEY_PATH="$HOME/.ssh/azure_vm_key"
echo "Using hardcoded SSH key: $SSH_KEY_PATH"

if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "WARNING: SSH key file not found at $SSH_KEY_PATH."
    echo "Please make sure you've properly set up your SSH key."
    exit 1
    SSH_KEY_OPT="-i $SSH_KEY_PATH"
fi

echo
echo "=== Setting Up Docker on VM ==="
echo "Installing Docker on the VM (if not already installed)..."

# Try to connect with the provided key or default settings
ssh -o StrictHostKeyChecking=no $SSH_KEY_OPT "$ADMIN_USERNAME@$VM_IP" "
  if ! command -v docker &> /dev/null; then
    echo 'Docker not found. Installing Docker...'
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\"
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo 'Docker installed successfully!'
  else
    echo 'Docker already installed.'
  fi
"

echo
echo "=== Opening Required Ports ==="
echo "Ensuring ports 8050 and 8888 are open..."
az vm open-port --port 8050 --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --priority 1001 || true
az vm open-port --port 8888 --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --priority 1002 || true

echo
echo "=== Uploading Docker Image ==="
echo "Uploading Docker image to the VM (this may take a while)..."
scp -o StrictHostKeyChecking=no $SSH_KEY_OPT "$DOCKER_IMAGE_NAME.tar" "$ADMIN_USERNAME@$VM_IP:~/"

echo
echo "=== Loading and Running Docker Container ==="
echo "Loading Docker image and starting container on the VM..."
ssh -o StrictHostKeyChecking=no $SSH_KEY_OPT "$ADMIN_USERNAME@$VM_IP" "
  docker load -i ~/$DOCKER_IMAGE_NAME.tar
  
  # Check if the image architecture matches the VM architecture
  CONTAINER_ARCH=\$(docker image inspect $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG --format='{{.Architecture}}')
  HOST_ARCH=\$(uname -m)
  echo \"Container architecture: \$CONTAINER_ARCH\" 
  echo \"Host architecture: \$HOST_ARCH\"
  if [[ \"$CONTAINER_ARCH\" != \"amd64\" || \"$HOST_ARCH\" != \"x86_64\" ]]; then
    echo \"WARNING: Container or host architecture may not match expected amd64/x86_64.\"
    echo \"This might cause performance issues or errors.\"
  fi
  
  # Stop existing container if it exists
  docker stop navegador-dashboard 2>/dev/null || true
  docker rm navegador-dashboard 2>/dev/null || true
  
  # Run new container
  docker run -d --name navegador-dashboard \
    -p 8050:8050 -p 8888:8888 \
    -e PYTHONPATH=/workspaces/navegador \
    --restart unless-stopped \
    $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG
"

echo
echo "===== Deployment Complete ====="
echo "Navegador Dashboard is now running on Azure VM: $VM_IP"
echo
echo "Access the dashboard at: http://$VM_IP:8050"
echo "Access Jupyter notebooks at: http://$VM_IP:8888"
echo
echo "SSH into the VM with: ssh $SSH_KEY_OPT $ADMIN_USERNAME@$VM_IP"
echo
echo "To stop the container: ssh $SSH_KEY_OPT $ADMIN_USERNAME@$VM_IP 'docker stop navegador-dashboard'"
echo "To start the container: ssh $SSH_KEY_OPT $ADMIN_USERNAME@$VM_IP 'docker start navegador-dashboard'"
