#!/usr/bin/env python3
import subprocess
import json
import re
import argparse

MAX_NAME_COL_WIDTH = 80

def parse_arguments():
    """Parses command-line arguments"""
    parser = argparse.ArgumentParser(description='Kubernetes Resource Reporter')
    parser.add_argument('-n', '--namespace',
                      help='Filter pods by specific namespace',
                      default=None)
    parser.add_argument('--wide',
                      help='Show wide output including node resources',
                      action='store_true')
    return parser.parse_args()

def get_pod_data(namespace=None):
    """Retrieves pod data in JSON format"""
    cmd = ["kubectl", "get", "pods", "-o", "json"]
    if namespace:
        cmd.extend(["-n", namespace])
    else:
        cmd.append("-A")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting pod data: {result.stderr}")
        exit(1)
    return json.loads(result.stdout)

def get_node_data():
    """Retrieves node data in JSON format"""
    cmd = ["kubectl", "get", "nodes", "-o", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting node data: {result.stderr}")
        exit(1)
    return json.loads(result.stdout)

def convert_cpu_to_millicores(cpu_value):
    """Converts CPU value to millicores (handles 500m and 0.5)"""
    if cpu_value == 'N/A':
        return 0

    if isinstance(cpu_value, str):
        num_str = re.sub(r'[^\d.-]', '', cpu_value.lower())
        if not num_str:
            return 0
        try:
            num = float(num_str)
        except ValueError:
            return 0

        if 'm' in cpu_value.lower():
            return num
        else:
            return num * 1000
    return float(cpu_value) * 1000

def convert_memory_to_mebibytes(memory_value):
    """Converts memory value to Mebibytes (MiB)"""
    if memory_value == 'N/A':
        return 0

    if isinstance(memory_value, str):
        memory_value = memory_value.upper()
        if 'GI' in memory_value:
            num = float(re.sub(r'[^\d.-]', '', memory_value))
            return num * 1024
        elif 'MI' in memory_value:
            num = float(re.sub(r'[^\d.-]', '', memory_value))
            return num
        elif 'KI' in memory_value:
            num = float(re.sub(r'[^\d.-]', '', memory_value))
            return num / 1024
        else:
            try:
                return float(memory_value) / (1024 * 1024)
            except ValueError:
                return 0
    try:
        return float(memory_value) / (1024 * 1024)
    except ValueError:
        return 0

def parse_container_resources(pod_data):
    """Parses container resource requests and returns usage statistics"""
    containers = []
    total_cpu_millicores = 0.0
    total_memory_mebibytes = 0.0

    for item in pod_data['items']:
        namespace = item['metadata']['namespace']
        pod_name = item['metadata']['name']
        node_name = item['spec'].get('nodeName', 'N/A')
        for container in item['spec']['containers']:
            requests = container.get('resources', {}).get('requests', {})
            cpu = requests.get('cpu', 'N/A')
            memory = requests.get('memory', 'N/A')

            cpu_millicores = convert_cpu_to_millicores(cpu)
            memory_mebibytes = convert_memory_to_mebibytes(memory)

            full_name = f"{namespace}/{pod_name}/{container['name']}"
            containers.append({
                'full_name': full_name,
                'node_name': node_name,
                'cpu': cpu,
                'memory': memory,
                'cpu_millicores': cpu_millicores,
                'memory_mebibytes': memory_mebibytes
            })

            total_cpu_millicores += cpu_millicores
            total_memory_mebibytes += memory_mebibytes

    return containers, total_cpu_millicores, total_memory_mebibytes

def get_node_resources():
    """Gets CPU and memory resources for all worker nodes"""
    node_data = get_node_data()
    node_resources = {}

    for node in node_data['items']:
        name = node['metadata']['name']
        if 'node-role.kubernetes.io/control-plane' in node['metadata'].get('labels', {}):
            continue  # Skip control-plane nodes

        allocatable = node['status']['allocatable']
        capacity = node['status']['capacity']

        node_resources[name] = {
            'allocatable_cpu': convert_cpu_to_millicores(allocatable.get('cpu', '0')),
            'allocatable_memory': convert_memory_to_mebibytes(allocatable.get('memory', '0')),
            'capacity_cpu': convert_cpu_to_millicores(capacity.get('cpu', '0')),
            'capacity_memory': convert_memory_to_mebibytes(capacity.get('memory', '0'))
        }

    return node_resources

def print_report(containers, total_cpu, total_memory, namespace_filter=None, wide=False):
    """Prints the report to the console"""
    title = "KUBERNETES RESOURCES REPORT"
    if namespace_filter:
        title += f" (namespace: {namespace_filter})"

    print(title)
    print("=" * 120)

    # Determine dynamic column width
    max_name_length = max((len(c['full_name']) for c in containers), default=30)
    name_col_width = min(max_name_length, MAX_NAME_COL_WIDTH)

    if wide:
        header_format = f"{{:<{name_col_width}}} {{:<15}} {{:<12}} {{:<12}} {{:>10}} {{:>12}}"
        row_format = f"{{:<{name_col_width}}} {{:<15}} {{:<12}} {{:<12}} {{:>8.0f}}m {{:>10.1f}}Mi"
        print(header_format.format("NAMESPACE/POD/CONTAINER", "NODE", "CPU (orig)", "MEM (orig)", "CPU (m)", "MEM (MiB)"))
    else:
        header_format = f"{{:<{name_col_width}}} {{:<12}} {{:<12}} {{:>10}} {{:>12}}"
        row_format = f"{{:<{name_col_width}}} {{:<12}} {{:<12}} {{:>8.0f}}m {{:>10.1f}}Mi"
        print(header_format.format("NAMESPACE/POD/CONTAINER", "CPU (orig)", "MEM (orig)", "CPU (m)", "MEM (MiB)"))

    print("-" * (name_col_width + (52 if not wide else 67)))

    for c in sorted(containers, key=lambda x: x['full_name']):
        name_trimmed = (c['full_name'][:name_col_width - 3] + '...') if len(c['full_name']) > name_col_width else c['full_name']
        if wide:
            print(row_format.format(
                name_trimmed,
                c['node_name'],
                str(c['cpu']),
                str(c['memory']),
                c['cpu_millicores'],
                c['memory_mebibytes']
            ))
        else:
            print(row_format.format(
                name_trimmed,
                str(c['cpu']),
                str(c['memory']),
                c['cpu_millicores'],
                c['memory_mebibytes']
            ))

    total_alloc_cpu = 0.0
    total_alloc_mem = 0.0
    total_capacity_cpu = 0.0
    total_capacity_mem = 0.0

    if wide:
        print("\nNODE RESOURCES:")
        print("=" * 120)
        node_resources = get_node_resources()
        if node_resources:
            print("{:<20} {:<15} {:<15} {:<15} {:<15}".format(
                "NODE NAME", "ALLOC CPU (m)", "ALLOC MEM (MiB)", "TOTAL CPU (m)", "TOTAL MEM (MiB)"))
            print("-" * 80)
            for node, resources in node_resources.items():
                print("{:<20} {:<15.0f} {:<15.1f} {:<15.0f} {:<15.1f}".format(
                    node,
                    resources['allocatable_cpu'],
                    resources['allocatable_memory'],
                    resources['capacity_cpu'],
                    resources['capacity_memory']))

                # Sum up all node resources
                total_alloc_cpu += resources['allocatable_cpu']
                total_alloc_mem += resources['allocatable_memory']
                total_capacity_cpu += resources['capacity_cpu']
                total_capacity_mem += resources['capacity_memory']
        else:
            print("No worker node resources found")

    print("\nSUMMARY:")
    print("=" * 120)
    print(f"Total Container CPU Requests: {total_cpu:.0f}m ({total_cpu/1000:.2f} cores)")
    print(f"Total Container Memory Requests: {total_memory:.1f}MiB ({total_memory/1024:.2f}GiB)")

    if wide and node_resources:
        print("\nCluster Worker Node Resources:")
        print(f"Total Allocatable CPU: {total_alloc_cpu:.0f}m ({total_alloc_cpu/1000:.2f} cores)")
        print(f"Total Allocatable Memory: {total_alloc_mem:.1f}MiB ({total_alloc_mem/1024:.2f}GiB)")
        print(f"Total Node Capacity CPU: {total_capacity_cpu:.0f}m ({total_capacity_cpu/1000:.2f} cores)")
        print(f"Total Node Capacity Memory: {total_capacity_mem:.1f}MiB ({total_capacity_mem/1024:.2f}GiB)")

        # Calculate utilization percentages
        if total_alloc_cpu > 0:
            cpu_util = (total_cpu / total_alloc_cpu) * 100
            print(f"\nCPU Request Utilization: {cpu_util:.1f}% of allocatable")
        if total_alloc_mem > 0:
            mem_util = (total_memory / total_alloc_mem) * 100
            print(f"Memory Request Utilization: {mem_util:.1f}% of allocatable")

    print(f"\nContainers processed: {len(containers)}")

def main():
    args = parse_arguments()
    pod_data = get_pod_data(args.namespace)
    containers, total_cpu, total_memory = parse_container_resources(pod_data)
    print_report(containers, total_cpu, total_memory, args.namespace, args.wide)

if __name__ == "__main__":
    main()
