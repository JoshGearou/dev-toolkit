# Kubernetes Architecture Documentation

Comprehensive reference documentation for Kubernetes control plane, data plane, and terminology.

## Documents

### [Control Plane Architecture](./control-plane.md)
Exhaustive documentation of Kubernetes control plane components and extensibility.

**Contents:**
- **Core Components**
  - kube-apiserver (API management, request processing, storage)
  - etcd (distributed key-value store, Raft consensus, operations)
  - kube-scheduler (scheduling framework, plugins, configuration)
  - kube-controller-manager (all 36+ controllers)
  - cloud-controller-manager (cloud provider integration)

- **Extensibility Points** (Complete)
  - API Extensions (CRDs, API Aggregation, APF)
  - Admission Control (built-in controllers, webhooks, policies)
  - Scheduler Extensions (framework plugins, extenders, profiles)
  - Storage Extensions (CSI, snapshots, cloning, expansion)
  - Networking Extensions (CNI, network policies, service mesh)
  - Authentication & Authorization (strategies, RBAC, webhooks)
  - Resource Management (HPA, VPA, Cluster Autoscaler, quotas)
  - Additional Extensions (DRA, kubectl plugins, finalizers)

- **Architecture Diagrams**
  - Complete control plane architecture with HA
  - API request processing pipeline
  - Internal component architectures

- **Deep Dives**
  - API server internals (watch mechanism, concurrency control, pagination)
  - etcd operations (backup/restore, compaction, performance tuning)
  - Security architecture (audit logging, encryption at rest)
  - High availability patterns (leader election, quorum)
  - Performance and scalability tuning

### [Data Plane Architecture](./data-plane.md)
Exhaustive documentation of Kubernetes data plane components running on worker nodes.

**Contents:**
- **Core Components**
  - kubelet (pod lifecycle, health monitoring, volume management, status reporting)
  - kube-proxy (service implementation, proxy modes, session affinity)
  - Container Runtime (CRI, containerd, CRI-O, runtime classes)

- **Pod Lifecycle**
  - Pod phases and conditions
  - Container states
  - Init containers
  - Restart policies
  - Graceful termination
  - Pod disruptions

- **Container Runtime Interface (CRI)**
  - RuntimeService and ImageService APIs
  - Pod sandbox lifecycle
  - Image management
  - Runtime configuration

- **Networking**
  - Pod networking model
  - CNI (Container Network Interface)
  - CNI plugins (Flannel, Calico, Cilium, Weave)
  - Network policies
  - DNS (CoreDNS)

- **Storage**
  - Volume lifecycle (static and dynamic provisioning)
  - CSI (Container Storage Interface)
  - Volume types (ephemeral, persistent, host)
  - Volume modes and access modes

- **Resource Management**
  - Requests and limits
  - QoS classes (Guaranteed, Burstable, BestEffort)
  - Resource quotas and limit ranges
  - Node eviction

- **Security**
  - Security contexts (pod-level, container-level)
  - Linux capabilities
  - AppArmor, SELinux, seccomp

- **Observability**
  - Metrics (resource metrics, custom metrics)
  - Logging (container logs, centralized logging)
  - Events

### [Glossary](./glossary.md)
Complete alphabetical reference of Kubernetes terminology, concepts, and abbreviations.

**Contents:**
- **A-Z Definitions**: Comprehensive definitions of all Kubernetes terms
- **Abbreviations**: API, CNI, CRI, CSI, RBAC, etc.
- **Common Labels**: Standard labels (app.kubernetes.io/*, topology.kubernetes.io/*)
- **Common Annotations**: Standard annotations (kubectl, prometheus, security)
- **HTTP Status Codes**: API response codes and meanings
- **API Verbs**: get, list, watch, create, update, patch, delete
- **Resource Units**: CPU (millicores), memory (bytes), storage
- **Well-Known Values**:
  - Access modes (RWO, ROX, RWX, RWOP)
  - Reclaim policies (Retain, Delete, Recycle)
  - Service types (ClusterIP, NodePort, LoadBalancer, ExternalName)
  - Probe types (httpGet, tcpSocket, exec, grpc)
  - Update strategies (RollingUpdate, Recreate, OnDelete)
  - Finalizers and taints

### [Communication and Lifecycles](./communication-and-lifecycles.md)
End-to-end flows showing how control plane and data plane components interact throughout resource lifecycles.

**Contents:**
- **Communication Architecture**
  - Complete system view with authentication boundaries
  - Hub-and-spoke pattern (API server as central hub)
  - Component authentication methods
  - Watch mechanism deep dive

- **Component Interactions**
  - API server as central hub
  - Watch-based synchronization
  - Controller reconciliation pattern

- **Complete Lifecycles**
  - Pod lifecycle (end-to-end from kubectl to running pod)
  - Service lifecycle and traffic flow
  - Deployment rollout with progressive updates
  - Volume provisioning and attachment (CSI flow)

- **Security Flows**
  - Authentication flow (multiple methods)
  - Authorization flow (RBAC deep dive)
  - Complete request flow with security checkpoints
  - ServiceAccount token lifecycle
  - Network policy enforcement

- **Network Traffic Patterns**
  - Pod-to-pod communication
  - Service ClusterIP traffic flow
  - Ingress traffic routing

- **State Synchronization**
  - etcd watch and API server watch cache
  - Eventual consistency examples

- **Failure Scenarios**
  - API server failure (HA recovery)
  - etcd quorum loss and recovery
  - Node failure and pod eviction
  - Controller crash and leader election

### [Extension Points Guide](./extension-points-guide.md)
Complete decision guide for all Kubernetes extension mechanisms with official recommendations.

**Contents:**
- **API Extension Methods**
  - CRDs vs API Aggregation (when to use each)
  - ConfigMaps and Secrets (proper usage)
  - Trade-offs and decision trees

- **Admission Control**
  - Validating vs Mutating webhooks
  - ValidatingAdmissionPolicy (CEL) - recommended for simple validation
  - Pod Security Admission (replacement for PSP)
  - Performance considerations

- **Scheduler Extensions**
  - Scheduler Framework Plugins (recommended)
  - Scheduler Extenders (deprecated, maintenance mode)
  - Custom Schedulers
  - When to use each

- **Storage Extensions**
  - CSI (Container Storage Interface) - the standard
  - Migration from in-tree plugins
  - Volume snapshots

- **Network Extensions**
  - CNI plugin comparison (Calico, Cilium, Flannel, Weave)
  - Network Policies best practices

- **Authentication and Authorization**
  - Auth method comparison (client certs, OIDC, ServiceAccount tokens, webhooks)
  - RBAC vs Webhook vs ABAC
  - Best practices and recommendations

- **Compute Extensions**
  - Device Plugins (current standard)
  - Dynamic Resource Allocation (future, alpha/beta)

- **Decision Matrix**
  - When to create a CRD
  - When to use webhooks vs built-in validation
  - Visual decision trees

- **Deprecated and Removed Features**
  - PodSecurityPolicy (removed 1.25)
  - Dockershim (removed 1.24)
  - In-tree plugins (being removed)
  - Migration guides

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CONTROL PLANE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ API Server   │  │  Scheduler   │  │ Controller      │  │
│  │              │  │              │  │ Manager         │  │
│  │ - Auth       │  │ - Filtering  │  │ - 36+ Ctrlrs    │  │
│  │ - Authz      │  │ - Scoring    │  │ - Reconcile     │  │
│  │ - Admission  │  │ - Binding    │  │ - Status Update │  │
│  └──────┬───────┘  └──────────────┘  └─────────────────┘  │
│         │                                                   │
│    ┌────▼────┐            ┌──────────────────┐            │
│    │  etcd   │            │ Cloud Controller │            │
│    │ Cluster │            │ Manager          │            │
│    └─────────┘            └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                        DATA PLANE                           │
│                      (Worker Nodes)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    kubelet                           │  │
│  │  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │  │
│  │  │ Sync Loop  │  │   PLEG   │  │ Volume Manager  │  │  │
│  │  │ Pod Worker │  │          │  │                 │  │  │
│  │  └─────┬──────┘  └──────────┘  └─────────────────┘  │  │
│  └────────┼─────────────────────────────────────────────┘  │
│           │                                                 │
│  ┌────────▼────────┐              ┌─────────────────────┐  │
│  │  Container      │              │   kube-proxy        │  │
│  │  Runtime (CRI)  │              │                     │  │
│  │  - containerd   │              │  - iptables/IPVS    │  │
│  │  - CRI-O        │              │  - Service routing  │  │
│  └────────┬────────┘              └─────────────────────┘  │
│           │                                                 │
│  ┌────────▼────────────────────────────────────────────┐   │
│  │                     Pods                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Pod 1    │  │ Pod 2    │  │ Pod 3    │  ...     │   │
│  │  │          │  │          │  │          │          │   │
│  │  │ [C1][C2] │  │ [C1]     │  │ [C1][C2] │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────┐              ┌─────────────────────┐  │
│  │  CNI Plugin     │              │  CSI Driver         │  │
│  │  - Networking   │              │  - Storage          │  │
│  └─────────────────┘              └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Control Plane
The control plane makes global decisions about the cluster (scheduling, scaling, responding to events). It consists of:
- **Decision makers**: API server, scheduler, controllers
- **State storage**: etcd
- **Cloud integration**: cloud-controller-manager

### Data Plane
The data plane executes workloads on worker nodes. It consists of:
- **Pod manager**: kubelet
- **Network proxy**: kube-proxy
- **Container execution**: Container runtime (containerd, CRI-O)
- **Infrastructure**: CNI plugins, CSI drivers, device plugins

### Communication Pattern
- **Hub and Spoke**: All components communicate through the API server
- **Watch-based**: Components watch resources rather than polling
- **Level-triggered**: Controllers continuously reconcile state
- **Declarative**: Users specify desired state, controllers implement it

## Extension Mechanisms

Kubernetes provides extensive extension points without modifying core code:

**API Level:**
- Custom Resource Definitions (CRDs)
- API Aggregation
- API Priority and Fairness

**Admission:**
- Mutating/Validating Webhooks
- Pod Security Admission

**Scheduling:**
- Scheduler Framework Plugins
- Custom Schedulers
- Scheduler Extenders

**Storage:**
- CSI Drivers
- Volume Snapshots

**Networking:**
- CNI Plugins
- Network Policies
- Service Mesh

**Compute:**
- Device Plugins
- Dynamic Resource Allocation (DRA)

**Security:**
- Authentication Webhooks
- Authorization Webhooks
- External Secret Management

## Design Principles

### Domain Driven Design
- **Ubiquitous Language**: Consistent terminology (Pod, Service, Volume)
- **Bounded Contexts**: API groups represent domain boundaries
- **Entities**: Objects with identity (Pods, Nodes)
- **Value Objects**: Immutable configuration (PodSpec, ServiceSpec)

### Reconciliation Loop
```
while true:
    desired_state = read_from_api_server()
    actual_state = observe_reality()
    if desired_state != actual_state:
        take_action_to_reconcile()
    sleep(interval)
```

### Eventual Consistency
- System converges toward desired state over time
- No strong consistency guarantees across distributed components
- etcd provides strong consistency for stored state

## Documentation Standards

These documents follow the project's documentation principles:
- **Mermaid diagrams**: Architecture visualization
- **Exhaustive coverage**: All components, features, and extension points
- **Code examples**: Configuration and code snippets
- **Domain focus**: IAM, access control, security emphasis
- **Operational details**: Configuration, tuning, troubleshooting

## Additional Resources

### Official Kubernetes Documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
- [Kubernetes Enhancement Proposals (KEPs)](https://github.com/kubernetes/enhancements)

### Specifications
- [Container Runtime Interface (CRI)](https://github.com/kubernetes/cri-api)
- [Container Network Interface (CNI)](https://github.com/containernetworking/cni)
- [Container Storage Interface (CSI)](https://github.com/container-storage-interface/spec)
- [OCI Runtime Specification](https://github.com/opencontainers/runtime-spec)

### Related Documentation in This Repository
- `iam/`: Identity and Access Management research
- `designs/`: Architecture documents and RFCs
- See [../CLAUDE.md](../CLAUDE.md) for repository guidelines
