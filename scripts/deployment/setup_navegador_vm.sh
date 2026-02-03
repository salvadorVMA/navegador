#!/bin/bash
# setup_navegador_vm.sh
# Run this script inside the navegador-dashboard-dev container on your Azure VM

set -e

# Activate conda environment
source /opt/conda/bin/activate nvg_py13_env

# Install required pip packages
pip install --upgrade pip
pip install streamlit==1.46.1 dash==3.0.4 anthropic==0.50.0 openai==1.76.2 tiktoken==0.9.0 \
  langchain==0.3.17 langchain-anthropic==0.3.12 langchain-community==0.3.16 \
  langchain-core==0.3.58 langchain-openai==0.3.15 langchain-text-splitters==0.3.8 \
  langchainhub==0.1.21 langgraph==0.4.1 langgraph-checkpoint==2.0.21 \
  langgraph-prebuilt==0.1.8 langgraph-sdk==0.1.64 langsmith==0.2.11 \
  chromadb==1.0.9 chroma-hnswlib==0.7.6 fastapi==0.115.9 uvicorn==0.32.1 \
  pydeck==0.9.1 geopandas==1.0.1 folium==0.14.0 altair==5.5.0 \
  dash-bootstrap-components==2.0.3 python-multipart==0.0.20 email-validator==2.2.0 \
  marshmallow==3.26.1 coloredlogs==15.0.1 humanfriendly==10.0 tabulate==0.9.0 \
  backoff==2.2.1 retrying==1.4.0 deprecated==1.2.13 overrides==7.4.0 wrapt==1.17.0 \
  memory-profiler==0.58.0 weasyprint==62.3 pypandoc==1.6.3

# Optional: Install VS Code server for remote development
if ! command -v code-server &> /dev/null; then
  curl -fsSL https://code-server.dev/install.sh | sh
fi

# Create two separate VS Code user-data directories
mkdir -p ~/.vscode1 ~/.vscode2

# Start two code-server instances on different ports
nohup code-server --bind-addr 0.0.0.0:8080 --user-data-dir ~/.vscode1 &
nohup code-server --bind-addr 0.0.0.0:8081 --user-data-dir ~/.vscode2 &

# Install Copilot, Codacy, and Git extensions in both sessions
for dir in ~/.vscode1 ~/.vscode2; do
  code-server --user-data-dir "$dir" --install-extension GitHub.copilot
  code-server --user-data-dir "$dir" --install-extension codacy.codacy-vscode
  code-server --user-data-dir "$dir" --install-extension GitHub.vscode-pull-request-github
done

cat << EOF

Setup complete!

Two independent VS Code code-server sessions are running:
  http://<vm-ip>:8080 (user-data-dir: ~/.vscode1)
  http://<vm-ip>:8081 (user-data-dir: ~/.vscode2)

Each session has Copilot, Codacy, and GitLens extensions installed.

To use VS Code Remote - SSH, open multiple windows and connect to the VM; each window can have its own workspace and Copilot session.

For true Copilot isolation, use different GitHub accounts in each session.

EOF
