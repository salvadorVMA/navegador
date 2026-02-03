FROM condaforge/mambaforge:latest

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and common CLI tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    ssh \
    rsync \
    gpg \
    lsof \
    net-tools \
    procps \
    tree \
    findutils \
    grep \
    zip \
    unzip \
    tar \
    gzip \
    bzip2 \
    xz-utils \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    sudo \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

# Install latest Node.js (LTS) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get update && apt-get install -y nodejs && npm install -g eslint



# Mambaforge already includes mamba and conda, no need to install Miniconda or mamba manually



# Set default shell to bash
SHELL ["/bin/bash", "-c"]

# Set working directory
WORKDIR /workspaces/navegador

# Expose port for dev server
EXPOSE 8000

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    openssh-client \
    vim \
    && rm -rf /var/lib/apt/lists/*




# Copy minimal conda environment file
COPY environment_min.yml .

# Create the minimal conda environment using mamba (already installed)
RUN mamba env create -f environment_min.yml -n nvg_py13_env



# Set up a non-root user for VS Code dev containers
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME

# Entrypoint
CMD ["bash"]

# Copy the rest of the application
COPY . .


# Create SSH directory for the vscode user
RUN mkdir -p /home/vscode/.ssh && chmod 700 /home/vscode/.ssh

# Set proper permissions (run as root before switching to USER vscode)
RUN chown -R vscode:vscode /workspaces/navegador || true && chown -R vscode:vscode /home/vscode/.ssh || true

# Expose additional ports
EXPOSE 8050 8888

# Set environment variables
ENV PYTHONPATH=/workspaces/navegador
ENV PATH="/opt/conda/envs/nvg_py13_env/bin:$PATH"

# Instructions: After container build, activate the environment and install pip packages
# Example:
# docker exec -it <container_id_or_name> bash
# source /opt/conda/bin/activate nvg_py13_env
# pip install streamlit==1.46.1 dash==3.0.4 anthropic==0.50.0 openai==1.76.2 tiktoken==0.9.0 \
#   langchain==0.3.17 langchain-anthropic==0.3.12 langchain-community==0.3.16 \
#   langchain-core==0.3.58 langchain-openai==0.3.15 langchain-text-splitters==0.3.8 \
#   langchainhub==0.1.21 langgraph==0.4.1 langgraph-checkpoint==2.0.21 \
#   langgraph-prebuilt==0.1.8 langgraph-sdk==0.1.64 langsmith==0.2.11 \
#   chromadb==1.0.9 chroma-hnswlib==0.7.6 fastapi==0.115.9 uvicorn==0.32.1 \
#   pydeck==0.9.1 geopandas==1.0.1 folium==0.14.0 altair==5.5.0 \
#   dash-bootstrap-components==2.0.3 python-multipart==0.0.20 email-validator==2.2.0 \
#   marshmallow==3.26.1 coloredlogs==15.0.1 humanfriendly==10.0 tabulate==0.9.0 \
#   backoff==2.2.1 retrying==1.4.0 deprecated==1.2.13 overrides==7.4.0 wrapt==1.17.0 \
#   memory-profiler==0.58.0 weasyprint==62.3 pypandoc==1.6.3
