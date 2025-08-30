# Debugging with Telepresence

This project uses [Telepresence](https://www.telepresence.io/) for debugging the HAProxy Template IC in a real Kubernetes environment. Telepresence allows you to run the controller locally while seamlessly accessing the cluster network.

## Requirements

### System Requirements
- **Operating System**: 
  - macOS (Intel or Apple Silicon)
  - Linux (x86_64)
  - Windows via WSL
- **kubectl** configured with access to your cluster
- Development environment running (`./scripts/start-dev-env.sh up`)

### Tool Installation
Choose one of the following installation methods:

#### Option 1: Direct Download
```bash
# Linux/macOS
curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o telepresence
chmod +x telepresence
sudo mv telepresence /usr/local/bin/
```

#### Option 2: Package Manager
```bash
# macOS via Homebrew
brew install datawire/blackbird/telepresence

# Arch Linux
yay -S telepresence2
```

## Quick Start

### Standard Workflow

1. **Start Development Environment**
   ```bash
   ./scripts/start-dev-env.sh up
   ```

2. **Enable Debug Mode**
   This puts the in-cluster controller to sleep and creates a development ConfigMap:
   ```bash
   ./scripts/start-dev-env.sh debug
   ```

3. **Connect via Telepresence**
   This establishes network connectivity to the cluster:
   ```bash
   ./scripts/start-dev-env.sh telepresence-connect
   ```

4. **Run Controller Locally**
   ```bash
   CONFIGMAP_NAME=haproxy-template-ic-config-dev SECRET_NAME=haproxy-template-ic-credentials \
   uv run haproxy-template-ic run
   ```

5. **Debug in Your IDE**
   - Open `haproxy_template_ic/__main__.py`
   - Set breakpoints where needed
   - Configure your IDE with the environment variables above
   - Run in Debug mode

### Using IntelliJ-based IDEs (PyCharm, IntelliJ, GoLand, etc.)

1. **Follow Standard Workflow** (steps 1-3 above)

2. **Configure Run Configuration**
   - Go to Run → Edit Configurations
   - Create a new Python configuration
   - Set Script path: `haproxy_template_ic/__main__.py`
   - Set Parameters: `run`
   - Set Environment variables:
     - `CONFIGMAP_NAME=haproxy-template-ic-config-dev`
     - `SECRET_NAME=haproxy-template-ic-credentials`
   - Set Working directory to your project root

3. **Debug**
   - Set breakpoints as needed
   - Click Debug button
   - The application runs locally with full cluster access

### Using VS Code

1. **Follow Standard Workflow** (steps 1-3 above)

2. **Configure launch.json**
   Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Debug HAProxy Template IC",
         "type": "python",
         "request": "launch",
         "module": "haproxy_template_ic",
         "args": ["run"],
         "env": {
           "CONFIGMAP_NAME": "haproxy-template-ic-config-dev",
           "SECRET_NAME": "haproxy-template-ic-credentials"
         },
         "console": "integratedTerminal"
       }
     ]
   }
   ```

3. **Debug**
   - Set breakpoints as needed
   - Press F5 or use Debug view
   - The application runs locally with full cluster access

## How It Works

Telepresence creates a bidirectional network connection between your local development machine and the Kubernetes cluster:

- **Traffic Manager**: Installed in the cluster to manage connections and routing
- **Local Daemon**: Runs on your machine to establish the secure tunnel
- **DNS Resolution**: Cluster services are accessible via their DNS names (e.g., `haproxy-template-ic:5555`)
- **Network Access**: Your local process can reach any service in the cluster
- **Volume Mounting**: ConfigMaps and Secrets are accessible from the cluster

The debug mode setup:
1. **Sleep Mode**: The in-cluster controller is set to sleep (`/usr/bin/sleep infinity`)
2. **Development ConfigMap**: A special ConfigMap points validation to the service name instead of localhost
3. **Local Socket**: Management socket is created locally as `mgmt.sock` for easy access
4. **Cluster Access**: Local controller accesses all cluster resources as if running inside

## Configuration

The development workflow uses two key configurations:

### 1. Development ConfigMap (`haproxy-template-ic-config-dev`)
Key differences from production ConfigMap:
- `validation.dataplane_host: haproxy-template-ic` (uses K8s service name)
- `operator.socket_path: mgmt.sock` (local file instead of `/run/haproxy-template-ic/management.sock`)

### 2. Debug Mode Deployment Patch
The sleep mode patch:
```yaml
spec:
  template:
    spec:
      containers:
        - name: controller
          command: ["/usr/bin/sleep"]
          args: ["infinity"]
          env:
            - name: CONFIGMAP_NAME
              value: haproxy-template-ic-config-dev
```

## Debugging Workflow

1. **Set Breakpoints**: Place breakpoints in your local code
2. **Start Debug Environment**: 
   ```bash
   ./scripts/start-dev-env.sh up
   ./scripts/start-dev-env.sh debug
   ./scripts/start-dev-env.sh telepresence-connect
   ```
3. **Run Locally**: Start the controller with development settings
4. **Interact with the Application**: 
   - Use `kubectl` to create/modify resources
   - Access validation services via Telepresence networking
   - All cluster resources are accessible to your local process
5. **Inspect State**: Use your IDE's debugger, management socket, or logs
6. **Clean Up**: 
   ```bash
   ./scripts/start-dev-env.sh telepresence-disconnect
   ./scripts/start-dev-env.sh no-debug
   ```

## Advantages Over Remote Debugging

- **No Docker Rebuilds**: Code changes are immediate - just restart locally
- **No Port Forwarding**: Services accessible via cluster DNS names
- **Full IDE Support**: Complete debugging experience with breakpoints, watches, etc.
- **Fast Iteration**: Change code, restart process - no image builds or pod restarts
- **Real Environment**: Test with actual cluster resources and network topology
- **Local Debugging Tools**: Management socket (`mgmt.sock`) available locally

## Management Socket Access

When running locally, the management socket is created as `mgmt.sock` in your project directory:

```bash
# Inspect runtime state
socat - UNIX-CONNECT:mgmt.sock
# Then type commands like: dump all, get maps host.map, etc.
```

## Troubleshooting

### Connection Issues
- **Check cluster access**: `kubectl get pods -n haproxy-template-ic`
- **Verify Telepresence status**: `./scripts/start-dev-env.sh telepresence-status`
- **Test service resolution**: `nslookup haproxy-template-ic` (should resolve to cluster IP)

### Debug Mode Issues
- **Controller still running**: Check if sleep mode applied: `kubectl get pods -n haproxy-template-ic -o wide`
- **ConfigMap not found**: Verify dev ConfigMap exists: `kubectl get configmap -n haproxy-template-ic`
- **Environment variables**: Ensure `CONFIGMAP_NAME` and `SECRET_NAME` are set correctly

### Performance and Connectivity
- **Network latency**: Local-to-cluster calls have some latency overhead
- **DNS resolution**: All cluster services accessible via their DNS names
- **Validation endpoint**: Should be accessible at `haproxy-template-ic:5555`

## Additional Resources

- [Telepresence Documentation](https://www.telepresence.io/docs/)
- [Telepresence Quick Start](https://www.telepresence.io/docs/latest/quick-start/)
- [IntelliJ Telepresence Plugin](https://www.jetbrains.com/help/pycharm/telepresence.html)
- [Troubleshooting Telepresence](https://www.telepresence.io/docs/latest/troubleshooting/)