# Docker Setup Runbook - Linux

## Overview
This runbook provides step-by-step instructions for setting up Docker on Linux for development with Segmento services.

## Prerequisites
- Linux system (CentOS, RHEL, Fedora, or similar)
- Administrative access (sudo)
- Internet connection for downloads
- Package manager (dnf/yum/tdnf)

## Installation

:::note
If you run into network connectivity issues (host unresponsive, can't ping, lose the ability to `ssh` into your workstation, etc.) after the following, see "[Using Docker in your Azure Workstation](/guides/docker-in-azure-vm.md)".
:::

### 1. Install Docker Engine
On a LinkedIn Linux workstation (either physical or an Azure Virtual Workstation), install Docker using your package manager:

#### For CentOS:
```bash
sudo yum install docker-ce
```

#### For CBL Mariner:
```bash
sudo yum install moby-engine moby-cli
```

#### For Fedora/RHEL (with dnf):
```bash
sudo dnf install moby-engine moby-cli ca-certificates -y
```

### 2. Install Docker Compose Plugin
```bash
RPM="docker-compose-plugin-2.6.0-3"
curl -s -S -f -L -o "${RPM}.rpm" https://artifactory.corp.linkedin.com:8083/artifactory/TOOLS/docker/${RPM}.el7.x86_64.rpm
sudo tdnf install -y --nogpgcheck ./*.rpm && sudo yum clean all && rm ./*.rpm
```

### 3. Configure Docker Network
Configure alternate address pools for the default Docker network bridge:

```bash
sudo bash -c "echo '{
  \"bip\": \"192.168.254.1/24\",
  \"default-address-pools\": [
    {\"base\": \"192.168.0.0/16\", \"size\": 24},
    {\"base\": \"192.169.0.0/16\", \"size\": 24}
  ]
}' > /etc/docker/daemon.json"
```

### 4. Setup User Permissions
Configure rootless permissions for docker:

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

**Note**: If you're running Linux in a virtual machine, restart the VM for changes to take effect.

### 5. Enable and Start Docker Service
Automatically start Docker and enable it for system startup:

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker
```

### 6. Install Helper Tools
Install lazydocker for interactive container debugging:

```bash
curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash
```

## Building Segmento Services

### Build Services with Docker (Linux Only)
```bash
mint build && mint pre-release && mint image build
```

### Building Images When Not Working Right
If you encounter build issues, use this process:

1. Check in all your changed files (mint pre-release changes Cargo file versions)
2. Clean and rebuild:

```bash
./docker/run-docker.sh docker-clean
git stash
export DOCKER_BUILDKIT=0
mint build
mint pre-release
mint image build
git stash pop
```

## `mint` & Docker Integration

`mint` provides a set of subcommands for managing images in the context of the Multiproduct ecosystem. Under the hood, `mint` generates a configuration file at `.linkedin/tasks/image/build.yaml` containing `docker build` CLI invocations.

### Environment Variables
The `mint` image build commands can be influenced by Docker environment variables such as:
- `DOCKER_HOST` - Specify Docker daemon endpoint
- `DOCKER_BUILDKIT` - Enable/disable BuildKit (set to 0 to disable)

For more environment variables, refer to the [Docker documentation](https://docs.docker.com/engine/reference/commandline/cli/#environment-variables).

### Basic `mint` Commands
```bash
# View available image commands
mint image --help

# Build images
mint image build

# List built images
mint image list
```

## Usage

### Running Segmento Services

#### Option 1: Local Segmento with Docker Services
Run docker services with local segmento build:

```bash
mint docker-up-local
```

#### Option 2: Run Integration Tests
```bash
mint test-local
```

#### Option 3: All Prebuilt Docker Services
Run all services from docker images:

```bash
./docker/run-docker.sh docker-up-client
```

### Advanced Docker Operations

#### Start with Custom Configuration
Start segmento with 5 chunk fabric instances:
```bash
./docker/run-docker.sh docker-up nodes=5
```

#### Override Environment Variables
```bash
VERSION=0.0.110 CHUNK_FABRIC_HOSTNAME=${USER}-ld1.linkedin.biz mint docker-up
```

Or using mint with pass-through:
```bash
mint docker-up --pass-through "s=metadata-service s=replication-healing n=1"
```

#### Generate Docker Compose File
```bash
./docker/run-docker.sh generate-docker-compose
```

#### Clean Docker Resources
Clean docker resources (images, containers, networks, etc.):
```bash
./docker/run-docker.sh docker-clean
```

## Configuration

### LARE (LinkedIn Application Runtime Environment)
Segmento services use containerization with LinkedIn's provided contract for images (LARE). This environment is used by many of LinkedIn's internal services, tools, and libraries, allowing developers to publish applications with container images without code changes.

## Troubleshooting

### Certificate Issues with Spiral
If spiral setup fails with certificate-related errors:

```bash
sudo --preserve-env=PATH sh -c "mkdir -p /etc/lipki && trust-ca-tool create-trust-cfg -td /etc/lipki -td /etc/riddler -CF DATAVAULT_STG -CF LIPKI_EI -CF LIPKI_PROD -CF DATAVAULT_CORP -CF LINKEDIN_CA |tee /etc/lipki/trust_config.json | trust-ca-tool create-truststore -f -"
```

### Docker Service Issues
If Docker service fails to start:

```bash
# Check service status
sudo systemctl status docker

# Check logs
sudo journalctl -u docker.service

# Restart service
sudo systemctl restart docker
```

### Permission Issues
If you get permission denied errors:

```bash
# Ensure user is in docker group
groups $USER

# If docker group is missing, add it:
sudo usermod -aG docker $USER
newgrp docker  # Or logout and login again
```

### Network Issues
If containers can't communicate:

1. Check Docker networks:
   ```bash
   docker network ls
   docker network inspect bridge
   ```

2. Verify daemon configuration:
   ```bash
   sudo cat /etc/docker/daemon.json
   ```

3. Restart Docker after configuration changes:
   ```bash
   sudo systemctl restart docker
   ```

### Build Issues
If image builds are failing:

1. Clean Docker system:
   ```bash
   docker system prune -a
   ```

2. Check disk space:
   ```bash
   df -h
   ```

3. Disable BuildKit if needed:
   ```bash
   export DOCKER_BUILDKIT=0
   ```

## Verification Steps
1. Verify Docker installation: `docker --version`
2. Test container execution: `docker run hello-world`
3. Check service status: `sudo systemctl status docker`
4. Verify user permissions: `docker ps`
5. Test network configuration: `docker network ls`

## CI/CD Environment Information

### GitHub Actions
LinkedIn uses self-hosted runners for GitHub Actions, which allows management of the execution environment and preloading with LinkedIn certificates and configuration. Each runner uses Docker-in-Docker for container access.

### Legacy PCx Pipeline
The legacy PCx pipeline ("multiproduct-post-merge", etc.) runs on bare metal servers with one Docker instance per build server. Access is restricted to the `image-tool` utility by a `setgid` sticky bit.

### Environment Variables in CI
The same Docker environment variables work in CI environments, including `DOCKER_HOST` for connecting to different Docker daemons.

## Additional Resources
- [LinkedIn Container Documentation](http://go/containers)
- [Docker Engine Documentation](https://docs.docker.com/engine/)
- [LinkedIn Application Runtime Environment (LARE)](http://go/containers)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Environment Variables](https://docs.docker.com/engine/reference/commandline/cli/#environment-variables)
- [Using Docker in your Azure Workstation](/guides/docker-in-azure-vm.md)