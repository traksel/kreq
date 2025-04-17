# Kubernetes Resource Reporter (KReq)

A lightweight Python tool for analyzing resource requests (`resources.requests`) across Kubernetes pods and worker nodes.

## ✨ Features

- **Container-level reporting**:
  - Lists CPU/memory requests for all containers
  - Shows original values and normalized units (millicores, MiB)
  - Filters by namespace

- **Cluster-wide insights**:
  - Worker node resource capacity/allocatable (with `--wide`)
  - Utilization percentages (requests vs allocatable)
  - Total resource summaries

- **Formatted output**:
  - Dynamic column widths
  - Human-readable units (cores, GiB)
  - Color-friendly terminal output

## 📦 Installation

```bash
curl -L https://raw.githubusercontent.com/traksel/kreq/refs/tags/v1.0.0/kreq.py -o $HOME/.local/bin/kreq
chmod 0744 $HOME/.local/bin/kreq

kreq --help
```

## 🚀 Usage

### Basic Commands
```bash
# Show all containers in all namespaces
kreq

# Filter by namespace
kreq -n my-namespace

# Show with node resources (wide mode)
kreq --wide
```

### Example Output
```
KUBERNETES RESOURCES REPORT
========================================================================================================
NAMESPACE/POD/CONTAINER              CPU (orig)  MEM (orig)    CPU (m)    MEM (MiB)
--------------------------------------------------------------------------------------------------------
default/nginx-xyz/nginx              500m        128Mi          500        128.0
kube-system/coredns-abc/coredns      100m        70Mi           100        70.0

SUMMARY:
========================================================================================================
Total Container CPU Requests: 600m (0.60 cores)
Total Container Memory Requests: 198.0MiB (0.19GiB)

Cluster Worker Node Resources:
Total Allocatable CPU: 8000m (8.00 cores)
Total Allocatable Memory: 16384.0MiB (16.00GiB)

Containers processed: 2
```

## 🔧 Configuration

### Persistent Settings

Add to your `~/.bashrc` or shell config:
```bash
# Always show node resources
alias kreq='kreq --wide'
```

## 🛠️ Requirements

- **Python**: 3.6+
- **Kubernetes**: `kubectl` configured with cluster access
- **Permissions**: Read access to pods/nodes

## 📊 Metrics Collected

| Metric | Unit | Description |
|--------|------|-------------|
| CPU Requests | millicores | Normalized to 1000m = 1 core |
| Memory Requests | Mebibytes (MiB) | 1 MiB = 1024 KiB |
| Node Allocatable | MiB/millicores | Resources available for pods |
| Node Capacity | MiB/millicores | Physical node resources |

## ♻️ Uninstallation
```bash
rm ~/.local/bin/kreq
```

## 📜 License
MIT License - See [LICENSE](https://github.com/yourusername/kreq/blob/main/LICENSE) file.
