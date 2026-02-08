#!/bin/bash
set -u

source_required_file() {
    local filepath="$1"
    local prefix="$(date '+%Y.%m.%d:%H:%M:%S') - "

    if [[ "${DEBUG:-false}" == "true" ]]; then
        prefix+="${0}: ${BASH_SOURCE[1]}::${FUNCNAME[1]}::${BASH_LINENO[1]} - ${BASH_SOURCE[0]}::${FUNCNAME[0]}::${BASH_LINENO[0]} ->"
    fi

    echo "${prefix}sourcing ${filepath}" >&2

    if [[ -f "$filepath" ]]; then
        source "$filepath"
    else
        echo "${prefix} error: Required file $filepath not found." >&2
        exit 1
    fi
}

log_message() {
    local message="$1"
    local prefix="$(date '+%Y.%m.%d:%H:%M:%S') - "

    if [[ "${DEBUG:-false}" == "true" ]]; then
        prefix+="${log_file}: ${0}: ${BASH_SOURCE[1]}::${FUNCNAME[1]}::${BASH_LINENO[1]} - ${BASH_SOURCE[0]}::${FUNCNAME[0]}::${BASH_LINENO[0]} ->"
    fi

    echo "${prefix}${message}" | tee -a "${log_file}"
}

get_git_root() {
    local repo_root
    if ! repo_root=$(git rev-parse --is-inside-work-tree &>/dev/null); then
        echo "Error: Not inside a Git repository." >&2
        exit 1
    fi
    git rev-parse --show-toplevel
}

run_command_with_retry() {
    local command="$1"
    local should_fail="${2:-false}"
    local ignore_exit_status="${3:-false}"
    local retry_count=0
    local max_retries=5
    local fib1=10
    local fib2=10

    while true; do
        local command_output="Running: ${command} in $(pwd)"
        local separator
        separator=$(printf '%*s' "${#command_output}" '' | tr ' ' '-')

        log_message "${separator}"
        log_message "${command_output}"
        log_message "${separator}"

        if [[ "${should_fail}" == "true" ]]; then
            log_message "${command} :: Command expected to fail"
        fi

        local output
        output=$(bash -c "${command}" 2>&1)
        local command_exit_status=$?

        echo "${output}" | while IFS= read -r line; do
            log_message "${command} :: ${line}"
        done

        log_message "${command} :: exit code: {${command_exit_status}}"

        if [[ "${output}" == *"fatal"* || "${output}" == *"disconnect"* ]]; then
            if (( retry_count < max_retries )); then
                ((retry_count++))
                log_message "${command} :: Rate limit detected or connection issue. Retrying in ${fib1} seconds... (Retry ${retry_count}/${max_retries})"
                sleep "${fib1}"
                local new_delay=$((fib1 + fib2))
                fib1=$fib2
                fib2=$new_delay
                continue
            else
                log_message "${command} :: Maximum retries reached. Skipping command: ${command}"
                break
            fi
        fi

        if [[ "${ignore_exit_status}" == "true" ]]; then
            log_message "${command} :: exit code: {${command_exit_status}} :: Info: exit code ignored"
            return
        fi

        if [[ "${command_exit_status}" -ne 0 ]]; then
            if [[ "${should_fail}" == "true" && "${command_exit_status}" -eq 0 ]]; then
                log_message "${command} :: exit code: {${command_exit_status}} :: Error: unexpected success"
                exit 2
            elif [[ "${should_fail}" != "true" ]]; then
                log_message "${command} :: exit code: {${command_exit_status}} :: Error: unexpected failure"
                exit 1
            fi
        fi

        break
    done
}

check_bash_version() {
    local bash_version
    bash_version=$(bash --version | head -n 1 | awk '{print $4}')
    log_message "Bash version: $bash_version"

    if [[ "${bash_version:0:1}" -lt 3 ]]; then
        log_message "This script requires Bash version 3.0 or later. Please update your Bash version."
        return 1
    fi
}

check_volta_and_node() {
    log_message "Checking Node.js version requirements..."
    
    # Check if Volta is installed
    if ! command -v volta >/dev/null 2>&1; then
        log_message "Warning: Volta not installed"
        log_message "Install: curl https://get.volta.sh | bash"
        log_message "Falling back to system Node.js..."
    else
        log_message "✓ Found Volta: $(volta --version)"
        
        # Ensure recent Node.js version (22 LTS recommended, 18 minimum)
        volta install node@22 || volta install node@18 || log_message "Warning: Could not install Node.js 22/18"
    fi
    
    # Check Node.js version
    if ! command -v node >/dev/null 2>&1; then
        log_message "Error: Node.js is not installed"
        log_message "Install Node.js 18+: https://nodejs.org/"
        exit 1
    fi
    
    local node_version
    node_version=$(node --version | sed 's/v//')
    local major_version
    major_version=$(echo "$node_version" | cut -d. -f1)
    
    log_message "Node.js version: v${node_version}"
    
    if (( major_version < 18 )); then
        log_message "Error: Node.js 18+ required, found v${node_version}"
        log_message "Upgrade with Volta: volta install node@22  # Recommended LTS"
        log_message "Or minimum version: volta install node@18"
        log_message "Or install from: https://nodejs.org/"
        exit 1
    fi
    
    if (( major_version >= 22 )); then
        log_message "✓ Node.js version meets requirements (v${node_version} - LTS recommended)"
    else
        log_message "✓ Node.js version meets requirements (v${node_version})"
        log_message "  Note: Node.js 22 LTS is now available for improved performance"
    fi
    
    # Check npm
    if ! command -v npm >/dev/null 2>&1; then
        log_message "Error: npm is not installed"
        exit 1
    fi
    
    log_message "✓ Found npm: $(npm --version)"
}

check_dependency() {
    local cmd="$1"
    local install_msg="$2"
    
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_message "Error: $cmd is not installed"
        log_message "$install_msg"
        exit 1
    fi
    log_message "✓ Found $cmd: $(command -v $cmd)"
}

detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        *)          echo "unsupported" ;;
    esac
}

get_installed_version() {
    local version_cmd="$1"
    local version
    
    if version=$($version_cmd 2>/dev/null); then
        echo "$version"
    else
        echo "not installed"
    fi
}

cluster_exists() {
    local cluster_name="$1"
    if kind get clusters 2>/dev/null | grep -q "^${cluster_name}$"; then
        return 0
    else
        return 1
    fi
}

delete_cluster() {
    local cluster_name="$1"
    if cluster_exists "$cluster_name"; then
        log_message "Deleting cluster '${cluster_name}'..."
        run_command_with_retry "kind delete cluster --name=${cluster_name}"
        log_message "Cluster '${cluster_name}' deleted."
    else
        log_message "Cluster '${cluster_name}' does not exist. Nothing to delete."
    fi
}

create_cluster() {
    local cluster_name="$1"
    local cluster_config="$2"

    if cluster_exists "$cluster_name"; then
        log_message "error: cluster '${cluster_name}' already exists."
        exit 1
    fi

    log_message "Creating cluster '${cluster_name}' with config '${cluster_config}'..."
    run_command_with_retry "kind create cluster --config=${cluster_config} --name=${cluster_name}"

    if ! cluster_exists "$cluster_name"; then
        log_message "error: cluster '${cluster_name}' not created."
        exit 1
    fi

    log_message "Cluster '${cluster_name}' created."
}

wait_for_pod_ready() {
    local app_label="$1"
    local namespace="$2"
    log_message "Waiting for '${app_label}' pod in '${namespace}' to be ready..."
    kubectl wait --for=condition=ready pod -l app="${app_label}" -n "${namespace}" --timeout=120s
}

start_port_forward() {
    local service="$1"
    local local_port="$2"
    local remote_port="$3"
    nohup kubectl port-forward "service/${service}" "${local_port}:${remote_port}" > /dev/null 2>&1 &
    port_forward_pid=$!
    log_message "Port-forwarding ${service} on ${local_port}:${remote_port} (PID ${port_forward_pid})"
    sleep 2
}

test_curl_endpoint() {
    local url="$1"
    run_command_with_retry "curl ${url}"
}

test_should_fail_curl_endpoint() {
    local url="$1"
    run_command_with_retry "curl ${url}" true
}

stop_port_forward() {
    if [[ -n "$port_forward_pid" && $(ps -p "$port_forward_pid" -o pid=) ]]; then
        run_command_with_retry "kill $port_forward_pid"
        wait "$port_forward_pid" 2>/dev/null
        log_message "Port-forward process ${port_forward_pid} terminated."
    else
        log_message "Port-forward process ${port_forward_pid} not found."
    fi
}

get_running_clusters() {
    kubectl config get-clusters | tail -n +2
}

get_namespaces() {
    kubectl get namespaces -o jsonpath="{.items[*].metadata.name}"
}

get_pods_in_namespace() {
    local namespace="$1"
    kubectl get pods -n "${namespace}" -o jsonpath="{.items[*].metadata.name}"
}

get_service() {
    local service_name="$1"
    local namespace="$2"
    kubectl get service "${service_name}" -n "${namespace}"
}

get_service_ports() {
    local service_name="$1"
    local namespace="$2"
    kubectl get service "${service_name}" -n "${namespace}" -o jsonpath="{.spec.ports[*].nodePort}"
}

get_nodes() {
    kubectl get nodes -o wide
}

get_control_plane_ip() {
    kubectl get nodes -o wide | grep control-plane | awk '{print $6}'
}

remove_docker_containers() {
    log_message "Listing all running Docker containers:"
    run_command_with_retry "docker ps"

    log_message "Stopping all running Docker containers..."
    local containers
    containers=$(docker ps -q 2>/dev/null)
    if [[ -n "$containers" ]]; then
        run_command_with_retry "docker stop $containers"
        log_message "Stopped containers: $containers"
    else
        log_message "No running containers to stop."
    fi

    log_message "Listing all containers (stopped and running):"
    run_command_with_retry "docker ps -a"

    log_message "Removing all Docker containers..."
    containers=$(docker ps -aq 2>/dev/null)
    if [[ -n "$containers" ]]; then
        run_command_with_retry "docker rm -f $containers"
        log_message "Removed containers: $containers"
    else
        log_message "No containers to remove."
    fi
}

remove_docker_images() {
    log_message "Listing all available Docker images:"
    run_command_with_retry "docker images"

    log_message "Removing all Docker images..."
    local images
    images=$(docker images -q 2>/dev/null)
    if [[ -n "$images" ]]; then
        while IFS= read -r image; do
            run_command_with_retry "docker rmi -f $image"
            log_message "Removed image: $image"
        done <<< "$images"
    else
        log_message "No images to remove."
    fi
}