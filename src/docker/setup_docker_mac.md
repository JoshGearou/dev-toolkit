# Docker Setup Runbook - macOS

## Overview
This runbook provides step-by-step instructions for setting up Docker on macOS for development with Segmento services.

## Prerequisites
- macOS system (Intel or Apple Silicon/M1)
- Administrative access to install software
- Internet connection for downloads

## Important Notes for Mac M1/Apple Silicon
- Mac M1 uses arm64 processor
- Docker on Mac currently uses emulation and runs x86 Linux images
- Rust binaries built on Mac M1 won't run on docker
- To make Caspian run on Docker on Mac, pull official Caspian docker images from Artifactory or deploy a registry server on your Linux box

## Installation

### 1. Install Docker Desktop
1. Download Docker Desktop from [Docker's official site](https://docs.docker.com/desktop/mac/install/)
   - Choose the appropriate version:
     - Intel Chip: Docker Desktop for Mac with Intel chip
     - Apple Silicon: Docker Desktop for Mac with Apple chip

2. Install Docker Desktop by dragging it to Applications folder

3. Launch Docker Desktop from Applications

#### Important Licensing Information
Docker Desktop is **commercial** software from Docker Inc., therefore it requires a license to use.

**Good news**: Microsoft has purchased a **site-wide** license for all LinkedIn employees. You do not need to enter any registration or other details to use Docker Desktop.

### 2. Configure Docker Desktop Settings
1. Open Docker Desktop
2. Go to **Settings** → **Resources** → **Network**
3. **Check** the box: "Use Kernel network for UDP"
4. **Uncheck** the box: "Enable host network" (if checked)

### 3. Stop Previous Docker Services (if applicable)
If you previously installed `docker-mac-net-connect`, stop it before starting Docker Desktop:

```bash
sudo brew services stop chipmk/tap/docker-mac-net-connect
```

### 4. Configure Docker Network
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

### 5. Add User to Docker Group
Add yourself to the `docker` group so you can use the `docker` CLI without `sudo`:

```bash
sudo usermod -a -G docker $USER
```

**Note**: You may need to log out and log back in for group changes to take effect.

### 6. Install Helper Tools
Install lazydocker for interactive container debugging:

```bash
brew install jesseduffield/lazydocker/lazydocker
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
Run docker services with local segmento build (good for working on segmento or thick client):

```bash
mint docker-up-local
```

**Note**: You might need to run `mint docker-up-local` manually once before trying `mint test-local`.

#### Option 2: Run Integration Tests
```bash
mint test-local
```

#### Option 3: All Prebuilt Docker Services
Run all services from docker images (good for testing thick client without local segmento changes):

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
```bash
./docker/run-docker.sh docker-clean
```

## Troubleshooting

### Certificate Issues with Spiral
If spiral setup fails with certificate-related errors:

```bash
sudo phoenix --certs --force -c
```

### Docker Desktop Not Starting
1. Ensure Docker Desktop is properly installed in Applications
2. Check that previous docker services are stopped
3. Restart Docker Desktop
4. Verify network configuration settings

### DockerServiceNotRunning Error
If you experience `DockerServiceNotRunning` when trying to build images:

1. Open Docker Desktop
2. Go to **Settings** → **Advanced**
3. Select **System (requires password)** for privileged access
4. Enable **Allow the default Docker socket to be used**
5. Restart Docker Desktop

### Performance Issues
1. Allocate more resources to Docker Desktop:
   - Go to Settings → Resources
   - Increase Memory and CPU limits
2. Enable VirtioFS for better file sharing performance:
   - Go to Settings → General → "Use VirtioFS"

### Container Build Issues
If you're experiencing build issues and want to start fresh:

```bash
./docker/run-docker.sh docker-clean
git stash
export DOCKER_BUILDKIT=0
# Then rebuild your services
git stash pop
```

## Verification Steps
1. Verify Docker is running: `docker --version`
2. Test container execution: `docker run hello-world`
3. Check Docker Desktop status in the menu bar
4. Verify network configuration with `docker network ls`

## CI/CD Environment Information

### GitHub Actions
LinkedIn uses self-hosted runners for GitHub Actions, which allows management of the execution environment and preloading with LinkedIn certificates and configuration. Each runner uses Docker-in-Docker for container access.

### Environment Variables in CI
The same Docker environment variables work in CI environments, including `DOCKER_HOST` for connecting to different Docker daemons.

## Additional Resources
- [LinkedIn Container Documentation](http://go/containers)
- [Docker Desktop Documentation](https://docs.docker.com/desktop/mac/)
- [Docker Desktop FAQ](https://docs.docker.com/desktop/faqs/general/)
- [LinkedIn Application Runtime Environment (LARE)](http://go/containers)
- [Docker Environment Variables](https://docs.docker.com/engine/reference/commandline/cli/#environment-variables)