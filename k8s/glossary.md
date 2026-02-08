# Kubernetes Glossary - Complete Reference

## A

**ABAC (Attribute-Based Access Control)**
Authorization mode that grants access based on policies combining attributes (user attributes, resource attributes, environment attributes). Superseded by RBAC in modern deployments.

**Admission Controller**
Plugin that intercepts requests to the Kubernetes API server before object persistence. Can validate, mutate, or reject requests. Examples: NamespaceLifecycle, ResourceQuota, PodSecurity.

**Admission Webhook**
HTTP callback that receives admission requests and can mutate or validate resources. Two types: MutatingAdmissionWebhook and ValidatingAdmissionWebhook.

**Affinity**
Set of rules that provide hints about pod placement relative to other pods or nodes. Types include node affinity, pod affinity, and pod anti-affinity.

**Aggregation Layer (API Aggregation)**
Extension mechanism allowing custom API servers to integrate with the main Kubernetes API server, appearing as part of the unified API.

**Anti-Affinity**
Rules that repel pods from certain nodes or away from other pods. Used to spread replicas across failure domains.

**API Group**
Collection of related API resources. Examples: apps (Deployments, StatefulSets), batch (Jobs, CronJobs), rbac.authorization.k8s.io (Roles, RoleBindings).

**API Priority and Fairness (APF)**
Feature that manages API server request concurrency using priority levels and flow schemas to prevent overload and ensure fairness.

**API Server (kube-apiserver)**
Central control plane component that exposes the Kubernetes API. Only component with direct etcd access. Handles authentication, authorization, and admission control.

**APIService**
Resource that registers an aggregated API server with the main API server, defining which API group/version it serves.

**AppArmor**
Linux kernel security module that confines programs to limited resource sets. Can be applied to containers via annotations.

**Attach/Detach Controller**
Controller that attaches volumes to nodes before pods start and detaches them after pods terminate. Works with CSI and in-tree volume plugins.

**Audit Logging**
Feature that records API server requests for security analysis and compliance. Supports multiple backends (log files, webhooks) and configurable detail levels.

**Authentication**
Process of verifying client identity. Supports multiple strategies: client certificates, bearer tokens, OIDC, webhook, service account tokens.

**Authorization**
Process of determining if authenticated user can perform requested action. Modes include RBAC, ABAC, Webhook, Node authorization.

## B

**Baseline (Pod Security)**
Pod Security Standard that prevents known privilege escalations while maintaining broad compatibility. Sits between Privileged and Restricted.

**Bearer Token**
Authentication credential passed in HTTP Authorization header. Can be static tokens, bootstrap tokens, or service account tokens.

**Bind (Scheduler Plugin)**
Final phase where pod is assigned to node. Default creates Binding object in API server.

**Binding**
API object that represents pod-to-node assignment created by scheduler.

**Binding Cycle**
Asynchronous phase of scheduling where pod is bound to selected node. Includes Permit, PreBind, Bind, PostBind plugins.

**Bootstrap Token**
Special token used for node authentication during cluster join. Stored as Secrets in kube-system namespace.

**Bounded Context**
DDD concept: explicit boundary within which a domain model is defined and applicable. In Kubernetes, different API groups represent different bounded contexts.

## C

**CA (Certificate Authority)**
Entity that issues digital certificates. Kubernetes uses CAs for component authentication and TLS.

**Cascading Deletion**
Deletion strategy where dependents are automatically deleted when owner is deleted. Policies: Foreground, Background, Orphan.

**CEL (Common Expression Language)**
Language for expressing validation rules in CRDs and ValidatingAdmissionPolicies. Enables complex in-tree validation without webhooks.

**Certificate Signing Request (CSR)**
Resource representing request for signed certificate from cluster CA. Used for kubelet certificates, user certificates, etc.

**Client Certificate**
X.509 certificate used for mutual TLS authentication. Subject CN becomes username, O becomes groups.

**Cloud Controller Manager (cloud-controller-manager)**
Optional control plane component that integrates cloud provider-specific logic (load balancers, routes, volumes, nodes).

**Cluster Autoscaler**
Component that automatically adjusts cluster size by adding or removing nodes based on resource needs.

**ClusterRole**
Cluster-scoped RBAC role defining permissions on cluster-wide resources or across all namespaces.

**ClusterRoleBinding**
Grants ClusterRole permissions to subjects (users, groups, service accounts) across entire cluster.

**CNI (Container Network Interface)**
Standard for configuring network interfaces in Linux containers. Plugins provide pod networking.

**Compaction (etcd)**
Process of removing historical etcd revisions to reclaim space. Can be automatic or manual.

**ConfigMap**
API object storing non-confidential configuration data as key-value pairs. Can be consumed as environment variables, command-line arguments, or files.

**Container Runtime**
Software responsible for running containers. Kubernetes supports CRI-compatible runtimes (containerd, CRI-O, Docker via dockershim until 1.24).

**Container Storage Interface (CSI)**
Standard for exposing storage systems to container orchestrators. Replaced in-tree volume plugins.

**Controller**
Control loop that watches cluster state via API server and makes changes to move current state toward desired state.

**Controller Manager (kube-controller-manager)**
Control plane component running multiple controllers (Node, ReplicaSet, Endpoints, ServiceAccount, etc.).

**Conversion Webhook**
HTTP callback that converts custom resources between different API versions. Required for multi-version CRDs.

**Coordinated Leader Election**
Pattern where multiple instances compete for leadership using Lease objects. Only leader performs reconciliation.

**CRD (Custom Resource Definition)**
API extension that defines custom resource types with OpenAPI schemas. Stored in etcd.

**CRI (Container Runtime Interface)**
gRPC API for kubelet to communicate with container runtimes. Defines ImageService and RuntimeService.

**CronJob**
Workload that creates Jobs on repeating schedule specified using cron format.

**Custom Controller**
User-created controller that extends Kubernetes by watching resources and implementing custom business logic.

**Custom Metrics**
Metrics exposed via custom.metrics.k8s.io API for HPA. Typically sourced from application metrics (Prometheus, Datadog).

**Custom Resource (CR)**
Instance of Custom Resource Definition. Extends Kubernetes with domain-specific objects.

## D

**DaemonSet**
Workload that ensures pod runs on all (or selected subset of) nodes. Used for node-level services like log collectors, monitoring agents.

**Data Plane**
Cluster components that run containerized applications and handle network traffic (kubelet, kube-proxy, container runtime, pods).

**Declarative Configuration**
Approach where you describe desired state and controllers reconcile actual state. Contrast with imperative (issue commands).

**Default Storage Class**
StorageClass marked as default with annotation. Used when PVC doesn't specify storageClassName.

**Defragmentation (etcd)**
Process of rewriting etcd database to reclaim space after compaction. Temporarily increases resource usage.

**Deployment**
Workload that manages ReplicaSets and provides declarative updates for Pods. Supports rolling updates and rollbacks.

**Device Plugin**
gRPC service that advertises specialized hardware (GPUs, FPGAs, network devices) to kubelet and allocates them to containers.

**Disruption**
Voluntary or involuntary event causing pod termination. PodDisruptionBudgets limit voluntary disruptions.

**DNS (Cluster DNS)**
Service discovery mechanism. CoreDNS typically provides DNS for service and pod name resolution.

**Domain Driven Design (DDD)**
Software design approach emphasizing domain model and ubiquitous language. Kubernetes API groups follow DDD patterns.

**Downward API**
Mechanism for containers to access pod/container metadata via environment variables or files.

**DRA (Dynamic Resource Allocation)**
Next-generation mechanism for allocating specialized resources to pods. Replaces device plugins (alpha in 1.26+).

**Dry Run**
API server feature that validates requests without persisting changes to etcd. Useful for testing.

**Dynamic Admission Control**
Extensible admission control via webhooks. Allows external services to validate/mutate resources.

**Dynamic Provisioning**
Automatic PersistentVolume creation when PersistentVolumeClaim is created. Implemented by StorageClass provisioners.

## E

**Election Timeout (etcd)**
Duration after which etcd member triggers new leader election if no heartbeat from leader. Typically 1000ms.

**Encryption at Rest**
Feature encrypting resources (Secrets, ConfigMaps) in etcd. Supports AES, KMS providers.

**Endpoints**
API object listing IP addresses and ports of pods backing a Service. Being replaced by EndpointSlices.

**EndpointSlice**
Scalable replacement for Endpoints. Distributes large endpoint lists across multiple objects.

**Ephemeral Container**
Container added to running pod for debugging. Cannot be removed once added. Requires EphemeralContainers feature.

**Ephemeral Volume**
Volume with lifecycle tied to pod. Types: emptyDir, CSI ephemeral volumes, generic ephemeral volumes.

**etcd**
Distributed key-value store serving as Kubernetes' database. Stores all cluster state. Uses Raft consensus.

**Event**
Resource recording state changes and notable occurrences in cluster. Used for debugging and auditing.

**Eventual Consistency**
Model where system converges toward desired state over time. Kubernetes controllers implement this pattern.

**Eviction**
Proactive pod termination by kubelet (resource pressure) or user action. Respects PodDisruptionBudgets for voluntary evictions.

**External Metrics**
Metrics from systems outside cluster (cloud provider metrics, external monitoring). Exposed via external.metrics.k8s.io API for HPA.

**External Secrets Operator**
Operator that synchronizes secrets from external secret management systems (Vault, AWS Secrets Manager) to Kubernetes Secrets.

## F

**Finalizer**
String in object metadata preventing deletion until removed. Enables cleanup operations before object removal.

**Filter (Scheduler Plugin)**
Scheduling phase eliminating nodes that cannot run pod. All filters must pass for node to be feasible.

**FlowSchema**
API Priority and Fairness resource that classifies requests and assigns them to priority levels.

**Foreground Deletion**
Cascading deletion mode where owner deleted after all dependents. Blocks until dependents removed.

**Fsync**
System call forcing write to disk. Critical for etcd durability. Should complete in <10ms.

## G

**Garbage Collection**
Automatic deletion of dependent objects when owner deleted. Implemented by garbage collector controller.

**Generic Ephemeral Volume**
Ephemeral volume defined inline using PVC template. Supports any storage class.

**Group (API Group)**
See API Group.

**GPU**
Graphics Processing Unit. Exposed to Kubernetes via device plugins or DRA.

## H

**HA (High Availability)**
Architecture with redundant components to eliminate single points of failure. Kubernetes control plane HA requires multiple API servers, etcd cluster, leader election.

**Headless Service**
Service with clusterIP: None. Returns pod IPs directly rather than load-balancing. Used for StatefulSets.

**Health Check**
Probe determining if application is healthy. Types: liveness, readiness, startup.

**Heartbeat**
Periodic signal from etcd follower to leader confirming connectivity. Default 100ms interval.

**Heartbeat (Node)**
Periodic update from kubelet to API server updating NodeStatus. Indicates node health.

**Horizontal Pod Autoscaler (HPA)**
Automatically scales number of pod replicas based on CPU, memory, or custom metrics.

**Host Network**
Pod networking mode using host's network namespace. Pod shares node's IP address.

**HostPath**
Volume type that mounts file or directory from host node filesystem into pod.

## I

**Image Pull Policy**
Policy controlling when kubelet pulls container image. Options: Always, IfNotPresent, Never.

**Image Pull Secret**
Secret containing credentials for private container registries. Referenced in pod spec or service account.

**Immutable**
Property of objects that cannot be modified after creation. ConfigMaps and Secrets can be marked immutable.

**Imperative Configuration**
Approach where you issue direct commands to cluster (kubectl create, kubectl delete). Contrast with declarative.

**Informer**
Client-go pattern combining watch and local cache for efficient resource monitoring.

**Ingress**
API object managing external HTTP(S) access to services. Typically implements virtual hosting and path-based routing.

**Ingress Controller**
Controller that implements Ingress resource functionality. Examples: nginx-ingress, Traefik, Contour.

**Init Container**
Container that runs before app containers. Used for setup tasks. Runs sequentially, must complete successfully.

**IPAM (IP Address Management)**
Component of CNI plugin responsible for allocating IP addresses to pods.

**IPTables**
Linux kernel feature for packet filtering and NAT. Default kube-proxy mode.

**IPVS (IP Virtual Server)**
Linux kernel load balancing technology. Alternative kube-proxy mode with better performance than iptables.

## J

**Job**
Workload that creates one or more pods and ensures specified number complete successfully. Used for batch processing.

**JSON Patch**
Format for describing changes to JSON documents. Used by mutating admission webhooks and kubectl patch.

**JWT (JSON Web Token)**
Token format used for service account tokens. Contains claims about identity and can be validated cryptographically.

## K

**KMS (Key Management Service)**
External service for encryption key management. Used with encryption at rest via KMS provider plugin.

**Kubeconfig**
Configuration file specifying clusters, users, and contexts for kubectl and other clients.

**Kubectl**
Command-line tool for interacting with Kubernetes clusters.

**Kubelet**
Node agent that ensures containers are running as specified in pod specs. Communicates with API server and container runtime.

**Kube-proxy**
Network proxy running on each node. Implements Service networking (iptables, ipvs, or userspace modes).

**Kubernetes API**
RESTful API exposing cluster resources and operations. Organized into API groups with versioning.

## L

**Label**
Key-value pair attached to objects. Used for organization, selection, and grouping. Queryable via label selectors.

**Label Selector**
Expression for selecting objects by labels. Supports equality-based and set-based selectors.

**Leader Election**
Process where multiple instances compete for single active leader using distributed coordination (Leases).

**Lease**
API object used for leader election and node heartbeats. Contains holder identity and timing information.

**Level-Triggered Reconciliation**
Controller pattern continuously syncing actual state to desired state based on current observations, not events.

**Limit Range**
Policy setting default, min, max resource requests/limits for containers and pods in namespace.

**Linearizability**
Strong consistency guarantee where operations appear instantaneous. etcd provides linearizable reads/writes.

**Liveness Probe**
Health check determining if container is alive. Kubelet restarts container if probe fails.

**Load Balancer**
Service type provisioning external load balancer (cloud provider). Also refers to components distributing traffic.

## M

**Managed Field**
Server-side apply concept tracking which manager owns each field in object.

**Manifest**
YAML or JSON file describing Kubernetes resource.

**Master**
Legacy term for control plane components. Replaced with "control plane" in modern documentation.

**Metadata**
Standard object fields: name, namespace, labels, annotations, etc.

**Metrics Server**
Cluster addon providing resource metrics (CPU, memory) via Metrics API. Required for HPA and VPA.

**Multi-tenancy**
Running multiple tenants (teams, applications) in single cluster with isolation.

**Mutating Admission Webhook**
Webhook that modifies resources before persistence. Returns JSON patch with changes.

**Mutual TLS (mTLS)**
Both client and server authenticate using certificates. Used between Kubernetes components.

## N

**Namespace**
Virtual cluster for resource isolation. Most resources are namespaced. Some (Nodes, PVs) are cluster-scoped.

**Network Policy**
Specification for pod network access control. Controls ingress and egress traffic.

**Node**
Worker machine (VM or physical) running kubelet, kube-proxy, and container runtime.

**Node Affinity**
Rules attracting pods to nodes with specific labels. Can be required or preferred.

**Node Authorization**
Authorization mode restricting kubelet permissions to only resources needed for its node.

**Node Controller**
Controller monitoring node health, marking unhealthy nodes, evicting pods from failed nodes.

**NodePort**
Service type exposing service on static port on each node's IP.

**Node Selector**
Simple label-based node selection. Superseded by node affinity for complex requirements.

**Normalize Score (Scheduler Plugin)**
Plugin point for normalizing scoring plugin outputs to 0-100 range and applying weights.

## O

**OIDC (OpenID Connect)**
Identity layer on top of OAuth 2.0. Kubernetes supports OIDC for user authentication.

**Operator**
Controller encoding domain-specific operational knowledge. Implements custom resource lifecycle.

**Optimistic Concurrency Control**
Conflict prevention using resourceVersion. Updates fail if version doesn't match.

**Orphan Deletion**
Deletion mode where owner deleted but dependents preserved. Requires --cascade=orphan.

**Out-of-Tree**
Components developed and released outside main Kubernetes codebase. Examples: cloud providers, CSI drivers.

**Owner Reference**
Metadata field linking dependent resource to owner. Enables garbage collection.

## P

**Patch**
API operation updating subset of resource fields. Supports JSON Patch, Merge Patch, Strategic Merge Patch.

**Persistent Volume (PV)**
Cluster resource representing storage. Provisioned statically or dynamically. Has lifecycle independent of pods.

**Persistent Volume Claim (PVC)**
Request for storage by user. Binds to matching PV. Specifies size, access mode, storage class.

**Permit (Scheduler Plugin)**
Plugin approving, denying, or waiting before binding pod to node. Used for gang scheduling.

**Pod**
Smallest deployable unit. Contains one or more containers sharing network and storage.

**Pod Affinity**
Rules attracting pods to run near other pods. Uses topology domains.

**Pod Anti-Affinity**
Rules repelling pods from other pods. Used to spread replicas.

**Pod Disruption Budget (PDB)**
Limits number of pods that can be voluntarily evicted. Ensures minimum availability during disruptions.

**Pod Overhead**
Resources reserved for pod infrastructure (runtime sandbox, sidecar). Defined in RuntimeClass.

**Pod Priority**
Integer value indicating pod importance. Higher priority pods scheduled first and can preempt lower priority.

**Pod Security Admission**
Built-in admission controller enforcing Pod Security Standards. Replaced PodSecurityPolicy.

**Pod Security Policy (PSP)**
Deprecated resource for pod security controls. Removed in 1.25. Replaced by Pod Security Admission.

**Pod Security Standards**
Three predefined security profiles: Privileged, Baseline, Restricted.

**Pod Topology Spread Constraints**
Declarative rules distributing pods across topology domains (zones, nodes, racks).

**PostBind (Scheduler Plugin)**
Informational plugin point after successful binding. Cannot fail binding.

**PreBind (Scheduler Plugin)**
Plugin performing operations before binding (provision volumes, reserve resources).

**Preemption**
Evicting lower priority pods to make room for higher priority pods. Implemented by PostFilter plugins.

**PreFilter (Scheduler Plugin)**
Plugin processing pod info before filtering. Can reject pod early if unsatisfiable.

**PreScore (Scheduler Plugin)**
Plugin pre-computing data shared by scoring plugins.

**PriorityClass**
Resource defining pod priority value and global default.

**PriorityLevelConfiguration**
API Priority and Fairness resource defining queue and concurrency settings for priority level.

**Privileged Container**
Container running with extended capabilities and host access. Security risk if not carefully controlled.

**Probe**
Health check executed by kubelet. Types: liveness, readiness, startup.

**Projected Volume**
Volume projecting multiple sources (secrets, configmaps, downward API, service account tokens) into single directory.

## Q

**QoS (Quality of Service)**
Pod classification affecting eviction order. Classes: Guaranteed, Burstable, BestEffort.

**Quorum**
Minimum number of etcd members required for operations. Formula: (N/2) + 1.

**Quota**
See Resource Quota.

**Queue Sort (Scheduler Plugin)**
Plugin determining pod ordering in scheduling queue.

## R

**Raft**
Consensus algorithm used by etcd for distributed coordination and leader election.

**RBAC (Role-Based Access Control)**
Authorization mode granting permissions based on roles assigned to users/groups/service accounts.

**Readiness Gate**
Custom condition checked before marking pod ready. Allows external systems to influence readiness.

**Readiness Probe**
Health check determining if pod can serve traffic. Failed probe removes pod from service endpoints.

**Reconciliation**
Controller pattern comparing desired state with actual state and making changes to align them.

**Reclaim Policy**
Policy for PV when PVC deleted. Options: Retain, Delete, Recycle (deprecated).

**ReplicaSet**
Workload maintaining stable set of pod replicas. Usually managed by Deployment.

**Replication Controller**
Legacy workload controller. Superseded by ReplicaSet.

**Reserve (Scheduler Plugin)**
Plugin maintaining state before binding. Can be reversed if binding fails.

**Resource**
API object type (Pod, Service, Deployment) or compute resource (CPU, memory).

**Resource Quota**
Policy limiting aggregate resource consumption per namespace.

**ResourceVersion**
Opaque string representing object version. Used for optimistic concurrency control and watch bookmarks.

**Restricted (Pod Security)**
Most restrictive Pod Security Standard. Enforces current pod hardening best practices.

**Revision**
etcd concept: monotonically increasing counter for database changes. Used for MVCC and watch.

**Role**
Namespace-scoped RBAC resource defining permissions.

**RoleBinding**
Grants Role permissions to subjects within namespace.

**Rolling Update**
Update strategy gradually replacing old pods with new ones. Default for Deployments and DaemonSets.

**RuntimeClass**
Resource specifying container runtime configuration. Supports overhead, scheduling constraints, runtime handler selection.

## S

**Sandbox**
Isolated environment for pod containers. Implementation varies by runtime (gVisor, Kata Containers, Firecracker).

**Scale (Subresource)**
Subresource enabling generic scale operations via kubectl scale. Supported by Deployment, ReplicaSet, StatefulSet.

**Scheduler (kube-scheduler)**
Control plane component assigning pods to nodes based on constraints and resource availability.

**Scheduler Extender**
HTTP webhook for custom scheduling logic. Less flexible than scheduling framework plugins.

**Scheduler Framework**
Plugin architecture for extending scheduler. Provides multiple extension points (Filter, Score, Bind, etc.).

**Scheduling Cycle**
Synchronous scheduling phase selecting node for pod. Includes PreFilter, Filter, Score, Reserve.

**Scheduling Profile**
Named scheduler configuration. Multiple profiles enable different scheduling policies in same cluster.

**Scope**
Resource attribute defining if resource is namespaced or cluster-scoped.

**Score (Scheduler Plugin)**
Plugin ranking feasible nodes on 0-100 scale. Combined with weights for final selection.

**Secret**
API object storing sensitive data (passwords, tokens, keys). Base64 encoded, optionally encrypted at rest.

**Secrets Store CSI Driver**
CSI driver mounting secrets from external systems (Vault, AWS Secrets Manager) as volumes.

**Security Context**
Pod or container-level security settings (runAsUser, capabilities, SELinux, AppArmor, seccomp).

**SELinux (Security-Enhanced Linux)**
Linux kernel security module providing mandatory access control. Configurable via security context.

**Selector**
See Label Selector or Field Selector.

**Server-Side Apply**
Declarative configuration with field-level conflict detection and management. Tracks field ownership.

**Service**
Abstraction exposing pods as network service. Provides stable IP and DNS name. Types: ClusterIP, NodePort, LoadBalancer, ExternalName.

**Service Account**
Identity for processes running in pods. Automatically mounted as projected volume.

**Service Account Token**
JWT authenticating service account. Bound to pod with audience and expiration.

**Service Mesh**
Infrastructure layer handling service-to-service communication (traffic management, security, observability). Examples: Istio, Linkerd.

**ServiceMonitor**
Prometheus Operator CRD defining scrape configuration for service endpoints.

**Sidecar Container**
Container running alongside main application container. Common pattern for cross-cutting concerns (logging, proxying).

**Snapshot**
Point-in-time copy of volume. Created via VolumeSnapshot resource. Requires CSI driver support.

**StatefulSet**
Workload for stateful applications requiring stable identities, persistent storage, ordered deployment/scaling.

**Static Pod**
Pod managed directly by kubelet (not API server). Defined by files in manifest directory.

**Status (Subresource)**
Subresource separating observed state from desired state. Updated by controllers.

**Storage Class**
Resource describing storage provisioner and parameters. Used for dynamic provisioning.

**Strategic Merge Patch**
Kubernetes-specific patch format with list merge strategies. Used by kubectl apply.

**Subject**
RBAC entity granted permissions. Can be User, Group, or ServiceAccount.

**SubjectAccessReview**
Resource checking if subject can perform action. Used by authorization webhooks.

**Sysctl**
Linux kernel parameter. Some safe sysctls can be set via pod security context.

## T

**Taint**
Key-value-effect tuple on node repelling pods without matching toleration. Effects: NoSchedule, PreferNoSchedule, NoExecute.

**TerminationGracePeriodSeconds**
Time kubelet waits after SIGTERM before sending SIGKILL. Default 30 seconds.

**Toleration**
Pod attribute allowing scheduling on tainted nodes despite taints.

**Topology**
Logical grouping of nodes. Common keys: topology.kubernetes.io/zone, topology.kubernetes.io/region, kubernetes.io/hostname.

**Topology Spread Constraints**
See Pod Topology Spread Constraints.

**TTL Controller**
Controller deleting resources after TTL expires. Used for finished Jobs, expired Secrets/ConfigMaps.

## U

**Ubiquitous Language**
DDD concept: shared vocabulary between domain experts and developers. Kubernetes APIs use ubiquitous language (Pod, Service, Volume).

**UID**
Unique identifier for object. Generated by API server on creation.

**Update Strategy**
Policy for updating workload pods. Types: RollingUpdate, OnDelete, Recreate.

## V

**Validating Admission Policy**
CEL-based in-tree validation rules. Alternative to validating webhooks (alpha in 1.26+).

**Validating Admission Webhook**
Webhook validating resources. Returns allow/deny decision with optional message.

**Value Object**
DDD concept: immutable object defined by attributes, not identity. Many Kubernetes specs are value objects.

**Vertical Pod Autoscaler (VPA)**
Automatically adjusts pod resource requests/limits based on usage. Modes: Off, Initial, Recreate, Auto.

**Version (API Version)**
API stability indicator. Levels: alpha (v1alpha1), beta (v1beta1), stable (v1, v2).

**Volume**
Directory accessible to containers in pod. Persists across container restarts. Types: emptyDir, hostPath, PVC, configMap, secret, projected, CSI.

**VolumeAttachment**
Resource representing volume-to-node attachment. Created by attach/detach controller.

**Volume Binding Mode**
StorageClass parameter controlling when PV binding occurs. Options: Immediate, WaitForFirstConsumer.

**VolumeSnapshot**
Resource representing volume snapshot. Requires VolumeSnapshotClass and CSI driver support.

**VolumeSnapshotClass**
Resource describing snapshot provisioner and parameters.

**VPA**
See Vertical Pod Autoscaler.

## W

**Watch**
API mechanism for streaming resource changes. More efficient than polling.

**Watch Cache**
API server cache enabling efficient watch operations. Configurable size per resource type.

**Webhook**
HTTP callback for extending Kubernetes. Types: admission webhooks, authentication webhooks, authorization webhooks, conversion webhooks.

**Workload**
Application running on Kubernetes. Controllers managing pods: Deployment, StatefulSet, DaemonSet, Job, CronJob.

## X

**X.509**
Standard for public key certificates. Used throughout Kubernetes for authentication and TLS.

## Z

**Zone**
Failure domain within cloud region. Typically represents data center or availability zone. Label: topology.kubernetes.io/zone.

---

## Abbreviations

- **API**: Application Programming Interface
- **APF**: API Priority and Fairness
- **CA**: Certificate Authority
- **CEL**: Common Expression Language
- **CNI**: Container Network Interface
- **CRD**: Custom Resource Definition
- **CRI**: Container Runtime Interface
- **CSI**: Container Storage Interface
- **CSR**: Certificate Signing Request
- **DDD**: Domain Driven Design
- **DNS**: Domain Name System
- **DRA**: Dynamic Resource Allocation
- **FPGA**: Field-Programmable Gate Array
- **GPU**: Graphics Processing Unit
- **HA**: High Availability
- **HPA**: Horizontal Pod Autoscaler
- **HTTP**: Hypertext Transfer Protocol
- **HTTPS**: HTTP Secure
- **IAM**: Identity and Access Management
- **IPAM**: IP Address Management
- **IPVS**: IP Virtual Server
- **JSON**: JavaScript Object Notation
- **JWT**: JSON Web Token
- **KEP**: Kubernetes Enhancement Proposal
- **KMS**: Key Management Service
- **MVCC**: Multi-Version Concurrency Control
- **NAT**: Network Address Translation
- **NFS**: Network File System
- **OIDC**: OpenID Connect
- **PDB**: Pod Disruption Budget
- **PV**: Persistent Volume
- **PVC**: Persistent Volume Claim
- **QoS**: Quality of Service
- **RBAC**: Role-Based Access Control
- **REST**: Representational State Transfer
- **SSD**: Solid State Drive
- **TLS**: Transport Layer Security
- **TTL**: Time To Live
- **UID**: Unique Identifier
- **VPA**: Vertical Pod Autoscaler
- **YAML**: YAML Ain't Markup Language

## Common Label Keys

- `app.kubernetes.io/name`: Application name
- `app.kubernetes.io/instance`: Application instance identifier
- `app.kubernetes.io/version`: Application version
- `app.kubernetes.io/component`: Component within architecture
- `app.kubernetes.io/part-of`: Application this is part of
- `app.kubernetes.io/managed-by`: Tool managing this resource
- `topology.kubernetes.io/zone`: Availability zone
- `topology.kubernetes.io/region`: Cloud region
- `kubernetes.io/hostname`: Node hostname
- `node.kubernetes.io/instance-type`: Node instance type

## Common Annotations

- `kubectl.kubernetes.io/last-applied-configuration`: Last applied configuration (kubectl apply)
- `kubernetes.io/ingress.class`: Ingress class (deprecated, use IngressClass)
- `prometheus.io/scrape`: Enable Prometheus scraping
- `prometheus.io/port`: Port for Prometheus scraping
- `prometheus.io/path`: Path for Prometheus scraping
- `container.apparmor.security.beta.kubernetes.io/<container>`: AppArmor profile
- `seccomp.security.alpha.kubernetes.io/pod`: Seccomp profile
- `scheduler.alpha.kubernetes.io/critical-pod`: Critical pod (legacy)

## HTTP Status Codes

- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid request (validation failed)
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authorization denied
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Conflict (resourceVersion mismatch)
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limited (APF)
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Temporarily unavailable

## Kubernetes API Verbs

- `get`: Retrieve specific resource
- `list`: Retrieve collection of resources
- `watch`: Stream resource changes
- `create`: Create new resource
- `update`: Replace existing resource
- `patch`: Partially update resource
- `delete`: Delete resource
- `deletecollection`: Delete multiple resources

## Access Modes (Persistent Volumes)

- `ReadWriteOnce (RWO)`: Single node read-write
- `ReadOnlyMany (ROX)`: Multiple nodes read-only
- `ReadWriteMany (RWX)`: Multiple nodes read-write
- `ReadWriteOncePod (RWOP)`: Single pod read-write (1.22+)

## Reclaim Policies

- `Retain`: Manually reclaim after PVC deletion
- `Delete`: Automatically delete storage
- `Recycle`: Scrub volume and make available (deprecated)

## Service Types

- `ClusterIP`: Internal cluster IP (default)
- `NodePort`: Expose on static port on each node
- `LoadBalancer`: Provision external load balancer
- `ExternalName`: Map to external DNS name

## Probe Types

- `httpGet`: HTTP GET request
- `tcpSocket`: TCP socket connection
- `exec`: Execute command in container
- `grpc`: gRPC health check (1.24+)

## Update Strategies

- `RollingUpdate`: Gradual replacement (Deployment, DaemonSet, StatefulSet)
- `Recreate`: Delete all pods, then create new (Deployment)
- `OnDelete`: Update only when manually deleted (DaemonSet, StatefulSet)

## Resource Units

- **CPU**: Millicores (m), 1 CPU = 1000m
- **Memory**: Bytes (E, P, T, G, M, K) or binary (Ei, Pi, Ti, Gi, Mi, Ki)
- **Storage**: Same as memory
- **Extended Resources**: Custom format (nvidia.com/gpu: 2)

## Well-Known Finalizers

- `kubernetes`: Standard Kubernetes finalizer
- `kubernetes.io/pv-protection`: PV protection
- `kubernetes.io/pvc-protection`: PVC protection
- `foregroundDeletion`: Foreground cascading deletion
- `orphan`: Orphan deletion

## Well-Known Taints

- `node.kubernetes.io/not-ready`: Node not ready
- `node.kubernetes.io/unreachable`: Node unreachable
- `node.kubernetes.io/out-of-disk`: Node out of disk
- `node.kubernetes.io/memory-pressure`: Memory pressure
- `node.kubernetes.io/disk-pressure`: Disk pressure
- `node.kubernetes.io/pid-pressure`: PID pressure
- `node.kubernetes.io/network-unavailable`: Network unavailable
- `node.kubernetes.io/unschedulable`: Node unschedulable
- `node.cloudprovider.kubernetes.io/uninitialized`: Cloud node not ready
