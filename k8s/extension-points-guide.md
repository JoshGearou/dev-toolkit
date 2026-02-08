# Kubernetes Extension Points - Complete Decision Guide

## Table of Contents

1. [Overview](#overview)
2. [API Extension Methods](#api-extension-methods)
3. [Admission Control](#admission-control)
4. [Scheduler Extensions](#scheduler-extensions)
5. [Storage Extensions](#storage-extensions)
6. [Network Extensions](#network-extensions)
7. [Authentication and Authorization](#authentication-and-authorization)
8. [Compute Extensions](#compute-extensions)
9. [Decision Matrix](#decision-matrix)
10. [Deprecated and Removed Features](#deprecated-and-removed-features)

## Overview

Kubernetes provides multiple extension points to add functionality without modifying core code. Choosing the right extension mechanism is critical for maintainability, performance, and upgrade compatibility.

### General Principles from Kubernetes SIG

**Prefer:**
- ✅ Standard extension points over forking
- ✅ Out-of-tree extensions over in-tree modifications
- ✅ Native resources over CRDs when possible
- ✅ CRDs over API Aggregation for most use cases
- ✅ Webhooks over custom admission controllers
- ✅ CSI over in-tree volume plugins
- ✅ CNI over custom networking solutions

**Avoid:**
- ❌ Forking Kubernetes
- ❌ Modifying core components
- ❌ In-tree plugins (deprecated)
- ❌ Direct etcd access
- ❌ Polling instead of watching

## API Extension Methods

### Custom Resource Definitions (CRDs)

**What:** Extend Kubernetes API with custom resource types stored in etcd.

**When to Use:**
- ✅ Modeling domain-specific resources (Databases, Applications, Configurations)
- ✅ Building operators and controllers
- ✅ Need declarative APIs
- ✅ Want kubectl integration
- ✅ Need RBAC integration
- ✅ Want API versioning and conversion

**When NOT to Use:**
- ❌ Need custom storage backend (use API Aggregation)
- ❌ Need complex non-REST semantics
- ❌ Need sub-millisecond read latency
- ❌ Have >100k instances of resource
- ❌ Need custom authentication/authorization per resource

**Kubernetes Recommendations:**

```yaml
# ✅ RECOMMENDED: Use structural schemas
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com
spec:
  versions:
  - name: v1
    schema:
      openAPIV3Schema:
        type: object  # ✅ Required for structural schema
        properties:
          spec:
            type: object
            # ✅ Explicit schema, not x-kubernetes-preserve-unknown-fields
```

**Best Practices:**
- ✅ **Use structural schemas** (required for pruning, defaulting, server-side apply)
- ✅ **Version your APIs** (v1alpha1 → v1beta1 → v1)
- ✅ **Provide conversion webhooks** for multi-version support
- ✅ **Use status subresources** (separate spec from status)
- ✅ **Use scale subresources** if resource is scalable
- ✅ **Add printer columns** for better kubectl output
- ✅ **Use CEL validation** (1.25+) instead of webhooks when possible
- ❌ **Avoid storing large objects** in CRDs (>1MB)
- ❌ **Don't use CRDs for high-churn data** (>10 updates/sec per instance)

**Official Guidance:**
> "CRDs are the recommended way to extend the Kubernetes API. They provide a declarative way to define new resource types and integrate seamlessly with kubectl, API machinery, and RBAC."
> - Kubernetes API Machinery SIG

### API Aggregation

**What:** Run custom API servers that integrate with kube-apiserver.

**When to Use:**
- ✅ Need custom storage backend (not etcd)
- ✅ Need complex API semantics beyond REST
- ✅ Need fine-grained control over API behavior
- ✅ Have specialized performance requirements
- ✅ Need custom authentication/authorization logic

**When NOT to Use:**
- ❌ Simple CRUD resources (use CRDs)
- ❌ Want easier deployment (CRDs are simpler)
- ❌ Need rapid development (CRDs faster to iterate)

**Examples:**
- ✅ Metrics Server (metrics.k8s.io)
- ✅ Custom Metrics Adapter (custom.metrics.k8s.io)
- ✅ Service Catalog (servicecatalog.k8s.io)

**Kubernetes Recommendations:**

```yaml
# ✅ Secure communication with API server
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1beta1.metrics.k8s.io
spec:
  service:
    name: metrics-server
    namespace: kube-system
  group: metrics.k8s.io
  version: v1beta1
  insecureSkipTLSVerify: false  # ✅ Always use TLS
  caBundle: <base64-ca>  # ✅ Provide CA bundle
  groupPriorityMinimum: 100
  versionPriority: 100
```

**Trade-offs:**

| Aspect | CRDs | API Aggregation |
|--------|------|-----------------|
| **Complexity** | Low | High |
| **Storage** | etcd only | Any backend |
| **API Semantics** | REST CRUD | Custom |
| **Deployment** | Simple (single YAML) | Complex (additional service) |
| **Performance** | Good for most | Optimized for use case |
| **Maintenance** | Lower | Higher |

**Official Guidance:**
> "Use CRDs if possible. Only use API Aggregation if you need custom storage, non-REST semantics, or have specific requirements that CRDs cannot meet."
> - Kubernetes API Machinery SIG

### ConfigMaps and Secrets

**What:** Native Kubernetes resources for configuration and sensitive data.

**When to Use:**
- ✅ Application configuration
- ✅ Environment variables
- ✅ Configuration files
- ✅ TLS certificates
- ✅ API keys, passwords (Secrets)

**When NOT to Use:**
- ❌ Complex application state (use CRDs)
- ❌ Structured data with validation (use CRDs)
- ❌ Data requiring versioning and conversion (use CRDs)
- ❌ High-security secrets (consider external secret managers)

**Kubernetes Recommendations:**

```yaml
# ✅ Use immutable ConfigMaps for better performance
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
immutable: true  # ✅ Reduces API server load, enables caching
data:
  config.yaml: |
    ...

---
# ✅ Use encryption at rest for Secrets
# Configure at cluster level
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:  # ✅ or aesgcm, secretbox, kms
      keys:
      - name: key1
        secret: <base64-key>
```

**Security Best Practices:**
- ✅ **Enable encryption at rest** for Secrets
- ✅ **Use RBAC** to restrict Secret access
- ✅ **Limit Secret scope** to specific namespaces
- ✅ **Consider external secret management** (Vault, AWS Secrets Manager)
- ✅ **Use External Secrets Operator** or Secrets Store CSI Driver
- ❌ **Don't store Secrets in git** (even encrypted)
- ❌ **Don't log Secret values**

## Admission Control

### Validating Admission Webhooks

**What:** External HTTPS callbacks that validate resources before persistence.

**When to Use:**
- ✅ Enforcing organizational policies
- ✅ Complex validation requiring external data
- ✅ Integration with external systems (CMDB, ITSM)
- ✅ Validation that cannot be expressed in CEL or OpenAPI

**When NOT to Use:**
- ❌ Simple validation (use CEL validation in CRDs)
- ❌ Performance-critical path (webhooks add latency)
- ❌ Can be done with OpenAPI schema validation

**Kubernetes Recommendations:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: example-webhook
webhooks:
- name: validate.example.com
  admissionReviewVersions: ["v1"]  # ✅ Use v1, not v1beta1
  sideEffects: None  # ✅ REQUIRED
  timeoutSeconds: 10  # ✅ Keep low (default 10s, max 30s)
  failurePolicy: Fail  # ✅ or Ignore for non-critical validation
  matchPolicy: Equivalent  # ✅ Recommended over Exact
  namespaceSelector:  # ✅ Scope to specific namespaces
    matchLabels:
      webhook: enabled
  objectSelector:  # ✅ Further narrow scope
    matchExpressions:
    - key: skip-validation
      operator: DoesNotExist
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["apps"]
    apiVersions: ["v1"]
    resources: ["deployments"]
    scope: "Namespaced"
```

**Best Practices:**
- ✅ **Set sideEffects: None** (required, indicates webhook has no side effects)
- ✅ **Keep timeouts low** (10s or less)
- ✅ **Use namespaceSelector** to avoid critical namespaces (kube-system)
- ✅ **Implement health checks** and monitoring
- ✅ **Use failurePolicy: Ignore** for non-critical validation (avoid blocking cluster)
- ✅ **Implement exponential backoff** in webhook server
- ✅ **Cache external data** to reduce latency
- ❌ **Don't make blocking external calls** that can timeout
- ❌ **Don't use for mutation** (use MutatingWebhook)

**Performance Impact:**
- Adds 10-500ms latency per request
- Can become bottleneck if slow or unavailable
- Consider impact on cluster operations

### Mutating Admission Webhooks

**What:** External HTTPS callbacks that modify resources before persistence.

**When to Use:**
- ✅ Injecting sidecar containers (service mesh, logging)
- ✅ Adding default values
- ✅ Adding labels/annotations for compliance
- ✅ Modifying security contexts
- ✅ Injecting volumes, environment variables

**When NOT to Use:**
- ❌ Can use PodPresets (deprecated, removed in 1.25)
- ❌ Can use CRD defaulting
- ❌ For validation only (use ValidatingWebhook)

**Kubernetes Recommendations:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: example-webhook
webhooks:
- name: mutate.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None  # ✅ REQUIRED
  reinvocationPolicy: Never  # ✅ or IfNeeded (use cautiously)
  timeoutSeconds: 10
  failurePolicy: Fail  # ⚠️ Consider Ignore for non-critical mutations
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
```

**Best Practices:**
- ✅ **Minimize mutations** (fewer changes = less complexity)
- ✅ **Be idempotent** (multiple calls should have same result)
- ✅ **Use reinvocationPolicy: Never** unless absolutely needed
- ✅ **Order matters** (mutating webhooks run alphabetically by name)
- ✅ **Return JSON Patch** format
- ❌ **Don't mutate and validate in same webhook** (separate webhooks)
- ❌ **Don't chain mutations** (use single webhook if possible)

**Official Guidance:**
> "Mutating webhooks can make debugging difficult. Minimize their use and prefer declarative defaults when possible."
> - Kubernetes API Machinery SIG

### ValidatingAdmissionPolicy (CEL)

**What:** In-tree validation using Common Expression Language (CEL).

**When to Use:**
- ✅ Simple validation rules (1.26+)
- ✅ Want to avoid webhook overhead
- ✅ Policy expressed as boolean conditions
- ✅ Need better performance than webhooks

**When NOT to Use:**
- ❌ Need external data or systems
- ❌ Complex logic not expressible in CEL
- ❌ Mutation required (use webhook)

**Kubernetes Recommendations:**

```yaml
# ✅ RECOMMENDED for simple validation (1.26+)
apiVersion: admissionregistration.k8s.io/v1alpha1
kind: ValidatingAdmissionPolicy
metadata:
  name: pod-security-policy
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
  validations:
  - expression: "!has(object.spec.hostNetwork) || !object.spec.hostNetwork"
    message: "HostNetwork is forbidden"
  - expression: "object.spec.containers.all(c, !has(c.securityContext.privileged) || !c.securityContext.privileged)"
    message: "Privileged containers are forbidden"
```

**Benefits over Webhooks:**
- ⚡ **Lower latency** (in-tree, no network call)
- 🔒 **More secure** (no external service)
- 🛠️ **Easier to manage** (no deployment required)
- 📊 **Better auditability** (policy in cluster)

**Official Guidance:**
> "ValidatingAdmissionPolicy with CEL is the future of policy validation. Use it instead of webhooks when possible for better performance and security."
> - Kubernetes API Machinery SIG

### Pod Security Admission

**What:** Built-in admission controller enforcing Pod Security Standards.

**When to Use:**
- ✅ Enforcing pod security policies (1.25+)
- ✅ Replacing PodSecurityPolicy (removed in 1.25)
- ✅ Cluster-wide or namespace security standards

**When NOT to Use:**
- ❌ Need fine-grained custom policies (use ValidatingWebhook or OPA)
- ❌ Kubernetes version < 1.22

**Kubernetes Recommendations:**

```yaml
# ✅ RECOMMENDED: Use namespace labels
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.28
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.28
```

**Standards:**
- **Privileged**: Unrestricted (no restrictions)
- **Baseline**: Minimally restrictive (prevents known privilege escalations)
- **Restricted**: Heavily restricted (current pod hardening best practices)

**Migration from PSP:**
- ❌ **PodSecurityPolicy removed in 1.25**
- ✅ **Migrate to Pod Security Admission**
- ✅ **Or use 3rd party policy engines** (OPA/Gatekeeper, Kyverno)

**Official Guidance:**
> "Pod Security Admission is the replacement for PodSecurityPolicy. Use the 'restricted' profile for production workloads when possible."
> - Kubernetes Auth SIG

## Scheduler Extensions

### Scheduler Framework Plugins

**What:** In-tree plugins extending scheduler behavior.

**When to Use:**
- ✅ Custom scheduling logic
- ✅ Need access to internal scheduler state
- ✅ Performance-critical scheduling decisions
- ✅ Want to contribute plugin upstream

**When NOT to Use:**
- ❌ External dependencies (use Scheduler Extender)
- ❌ Rapid iteration (requires recompilation)
- ❌ Don't want to maintain Go code

**Kubernetes Recommendations:**

```go
// ✅ Implement ScorePlugin interface
type CustomScorePlugin struct {
    handle framework.Handle
}

func (p *CustomScorePlugin) Score(
    ctx context.Context,
    state *framework.CycleState,
    pod *v1.Pod,
    nodeName string,
) (int64, *framework.Status) {
    // ✅ Return 0-100 score
    // ✅ Higher score = better fit
    return score, framework.NewStatus(framework.Success)
}
```

**Extension Points (in order):**
1. QueueSort
2. PreFilter
3. Filter
4. PostFilter (Preemption)
5. PreScore
6. Score
7. NormalizeScore
8. Reserve
9. Permit
10. PreBind
11. Bind
12. PostBind

**Best Practices:**
- ✅ **Keep plugins fast** (<10ms)
- ✅ **Use caching** for expensive operations
- ✅ **Return appropriate status codes**
- ❌ **Don't block** in plugin code
- ❌ **Don't make external API calls** in hot path

### Scheduler Extenders

**What:** HTTP webhooks for custom scheduling logic.

**When to Use:**
- ✅ Need external dependencies (databases, APIs)
- ✅ Rapid development/iteration
- ✅ Can't modify scheduler binary
- ✅ Written in non-Go language

**When NOT to Use:**
- ❌ Performance-critical (slower than plugins)
- ❌ Can use Scheduler Framework Plugins

**Kubernetes Recommendations:**

```yaml
# ⚠️ DEPRECATED: Consider Scheduler Framework instead
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
extenders:
- urlPrefix: "https://extender.example.com"
  filterVerb: "filter"
  prioritizeVerb: "prioritize"
  weight: 1
  enableHTTPS: true
  nodeCacheCapable: true
```

**Trade-offs:**

| Aspect | Scheduler Plugins | Scheduler Extenders |
|--------|-------------------|---------------------|
| **Performance** | Fast (in-process) | Slower (HTTP) |
| **Development** | Requires Go | Any language |
| **Deployment** | Scheduler restart | Independent service |
| **Complexity** | Medium | Lower |
| **Latency** | <1ms | 10-100ms |

**Official Guidance:**
> "Scheduler Extenders are in maintenance mode. New development should use the Scheduler Framework."
> - Kubernetes Scheduling SIG

### Custom Schedulers

**What:** Run additional schedulers alongside default scheduler.

**When to Use:**
- ✅ Specialized workloads (ML, batch processing)
- ✅ Completely different scheduling algorithms
- ✅ Testing new scheduling approaches

**When NOT to Use:**
- ❌ Can achieve with plugins or extenders
- ❌ Increases operational complexity

**Kubernetes Recommendations:**

```yaml
# ✅ Pod specifies scheduler
apiVersion: v1
kind: Pod
metadata:
  name: ml-workload
spec:
  schedulerName: ml-scheduler  # ✅ Use custom scheduler
  containers:
  - name: training
    image: ml-training:v1
```

**Best Practices:**
- ✅ **Use distinct scheduler names**
- ✅ **Implement leader election** for HA
- ✅ **Monitor scheduling latency**
- ❌ **Don't modify default scheduler**

## Storage Extensions

### Container Storage Interface (CSI)

**What:** Standard API for storage providers.

**When to Use:**
- ✅ ALL new storage providers (1.13+)
- ✅ Migrating from in-tree plugins

**When NOT to Use:**
- ❌ Using Kubernetes < 1.13
- ❌ Never (CSI is the standard)

**Kubernetes Recommendations:**

```yaml
# ✅ CSI Driver registration
apiVersion: storage.k8s.io/v1
kind: CSIDriver
metadata:
  name: ebs.csi.aws.com
spec:
  attachRequired: true
  podInfoOnMount: false
  volumeLifecycleModes:
  - Persistent
  - Ephemeral  # ✅ Support both if possible
  fsGroupPolicy: File
  storageCapacity: true  # ✅ Enable if driver supports
```

**Migration from In-Tree:**
- ❌ **In-tree plugins deprecated** (removed in 1.29+)
- ✅ **CSI Migration feature** provides compatibility
- ✅ **Enable CSIMigration feature gate**

**CSI Sidecars (Standard):**
- `external-provisioner`: Dynamic provisioning
- `external-attacher`: Volume attachment
- `external-resizer`: Volume expansion
- `external-snapshotter`: Volume snapshots
- `external-health-monitor`: Volume health
- `node-driver-registrar`: Node registration

**Best Practices:**
- ✅ **Implement CSI spec fully**
- ✅ **Support topology** for multi-zone
- ✅ **Implement volume snapshots**
- ✅ **Use gRPC for CSI**
- ✅ **Follow CSI sidecar versions**
- ❌ **Don't bypass CSI for storage operations**

**Official Guidance:**
> "CSI is the only supported way to add storage drivers. All in-tree volume plugins are deprecated."
> - Kubernetes Storage SIG

### Volume Snapshot

**What:** API for taking point-in-time snapshots.

**When to Use:**
- ✅ Backup and restore
- ✅ Clone volumes
- ✅ Disaster recovery

**Kubernetes Recommendations:**

```yaml
# ✅ Use VolumeSnapshot API
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: database-pvc
```

## Network Extensions

### Container Network Interface (CNI)

**What:** Standard API for network providers.

**When to Use:**
- ✅ ALL pod networking (CNI is the standard)

**Popular CNI Plugins:**

| Plugin | Use Case | Performance | Features |
|--------|----------|-------------|----------|
| **Calico** | General purpose, network policy | High | BGP, network policy, encryption |
| **Cilium** | eBPF, L7 policy, service mesh | Highest | eBPF, Hubble, service mesh |
| **Flannel** | Simple overlay | Medium | Simple, easy setup |
| **Weave** | Encryption, simplicity | Medium | Encryption, mesh |
| **Multus** | Multiple interfaces | N/A | SR-IOV, multiple networks |

**Kubernetes Recommendations:**

```json
// ✅ CNI Configuration
{
  "cniVersion": "0.4.0",  // ✅ Use latest CNI version
  "name": "k8s-pod-network",
  "plugins": [
    {
      "type": "calico",
      "ipam": {
        "type": "calico-ipam"  // ✅ Use plugin's IPAM
      }
    },
    {
      "type": "portmap",  // ✅ For hostPort support
      "capabilities": {"portMappings": true}
    },
    {
      "type": "bandwidth",  // ✅ For traffic shaping
      "capabilities": {"bandwidth": true}
    }
  ]
}
```

**Official Guidance:**
> "Choose a CNI plugin based on your requirements. Cilium is recommended for advanced features and performance. Calico for strong network policy. Flannel for simplicity."
> - Kubernetes Networking SIG

### Network Policies

**What:** Declarative rules for pod network traffic.

**When to Use:**
- ✅ Zero-trust networking
- ✅ Microsegmentation
- ✅ Compliance requirements

**Kubernetes Recommendations:**

```yaml
# ✅ Default deny-all, explicit allow
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}  # ✅ Applies to all pods
  policyTypes:
  - Ingress
  - Egress
# No ingress/egress rules = deny all

---
# ✅ Then add specific allow rules
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

**Best Practices:**
- ✅ **Start with default-deny**
- ✅ **Explicitly allow required traffic**
- ✅ **Use namespace selectors** for cross-namespace
- ✅ **Test policies** in staging
- ❌ **Don't forget egress** (DNS, external services)

## Authentication and Authorization

### Authentication Methods

**Comparison:**

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Client Certificates** | System components | Strong, no external deps | Key management, rotation |
| **OIDC** | Human users | Standard, SSO integration | Requires identity provider |
| **Service Account Tokens** | Pods, automation | Automatic, scoped | Limited to cluster |
| **Webhook** | Custom auth | Flexible | Latency, availability |
| **Bootstrap Tokens** | Node joining | Secure bootstrap | Time-limited |

**Kubernetes Recommendations:**

```yaml
# ✅ OIDC for human users
--oidc-issuer-url=https://accounts.google.com
--oidc-client-id=kubernetes
--oidc-username-claim=email
--oidc-groups-claim=groups

# ✅ Client certs for system components
--client-ca-file=/etc/kubernetes/pki/ca.crt

# ✅ Webhook for custom logic
--authentication-token-webhook-config-file=/etc/kubernetes/webhook-config.yaml
```

**Best Practices:**
- ✅ **Use OIDC for users** (Google, Azure AD, Okta)
- ✅ **Use client certs for components**
- ✅ **Use ServiceAccount tokens for pods**
- ✅ **Enable multiple auth methods**
- ❌ **Don't use static token files** (insecure)
- ❌ **Don't share credentials**

### Authorization Methods

**Comparison:**

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **RBAC** | Standard authz | Flexible, standard | Can be complex |
| **Webhook** | Custom authz, external | Integration with external systems | Latency, availability |
| **ABAC** | Legacy | Attribute-based | Deprecated, use RBAC |
| **Node** | Kubelet | Scoped to node | Only for kubelet |

**Kubernetes Recommendations:**

```yaml
# ✅ RECOMMENDED: RBAC
--authorization-mode=Node,RBAC

# ⚠️ Add Webhook only if needed
--authorization-mode=Node,RBAC,Webhook
```

**RBAC Best Practices:**
- ✅ **Principle of least privilege**
- ✅ **Use Roles for namespace scope**
- ✅ **Use ClusterRoles for cluster scope**
- ✅ **Group related permissions**
- ✅ **Use RoleBindings to grant access**
- ✅ **Audit permissions regularly**
- ❌ **Don't use cluster-admin except for bootstrap**
- ❌ **Don't grant * permissions broadly**

**Official Guidance:**
> "RBAC is the recommended authorization mode. ABAC is deprecated and should not be used for new clusters."
> - Kubernetes Auth SIG

## Compute Extensions

### Device Plugins

**What:** Expose specialized hardware to containers.

**When to Use:**
- ✅ GPUs (NVIDIA, AMD)
- ✅ FPGAs
- ✅ InfiniBand adapters
- ✅ Custom ASICs

**Kubernetes Recommendations:**

```go
// ✅ Implement DevicePlugin gRPC interface
type DevicePluginServer interface {
    GetDevicePluginOptions(context.Context, *Empty) (*DevicePluginOptions, error)
    ListAndWatch(*Empty, DevicePlugin_ListAndWatchServer) error
    Allocate(context.Context, *AllocateRequest) (*AllocateResponse, error)
    GetPreferredAllocation(context.Context, *PreferredAllocationRequest) (*PreferredAllocationResponse, error)
    PreStartContainer(context.Context, *PreStartContainerRequest) (*PreStartContainerResponse, error)
}
```

**Best Practices:**
- ✅ **Register with kubelet** via Unix socket
- ✅ **Implement health checks**
- ✅ **Handle pod deletion** properly
- ✅ **Report accurate device status**

### Dynamic Resource Allocation (DRA)

**What:** Next-generation device plugin replacement (alpha in 1.26+).

**When to Use:**
- ✅ Complex device sharing (slicing, partitioning)
- ✅ Device pools spanning nodes
- ✅ More than on-off device allocation

**When NOT to Use:**
- ❌ Production (still alpha/beta)
- ❌ Simple GPU allocation (device plugins work fine)

**Kubernetes Recommendations:**

```yaml
# ⚠️ ALPHA/BETA: Not for production yet
apiVersion: resource.k8s.io/v1alpha2
kind: ResourceClass
metadata:
  name: gpu-nvidia-a100
spec:
  driverName: gpu.nvidia.com
```

**Official Guidance:**
> "DRA is the future of device allocation. Device plugins will eventually be deprecated. However, DRA is not production-ready as of 1.28."
> - Kubernetes Node SIG

## Decision Matrix

### When to Create a CRD

```
┌─────────────────────────────────────────┐
│ Need to extend Kubernetes API?         │
└───────────┬─────────────────────────────┘
            ├─ Yes
            │  ┌────────────────────────────────────┐
            │  │ Need custom storage backend?       │
            │  └────┬──────────────────────────┬────┘
            │       ├─ Yes                     ├─ No
            │       │  Use API Aggregation     │  ┌──────────────────────────┐
            │       │                          │  │ Simple CRUD resources?   │
            │       │                          │  └─┬─────────────────────┬──┘
            │       │                          │    ├─ Yes              ├─ No
            │       │                          │    │  Use CRD          │  ┌─────────────────┐
            │       │                          │    │                   │  │ Complex logic?  │
            │       │                          │    │                   │  └─┬───────────┬───┘
            │       │                          │    │                   │    ├─ Yes      ├─ No
            │       │                          │    │                   │    │ Operator  │  CRD
            │       │                          │    │                   │    │ + CRD     │
            ├─ No
            │  ┌────────────────────────────────────┐
            │  │ Need configuration only?           │
            │  └────┬──────────────────────────┬────┘
            │       ├─ Sensitive data         ├─ Not sensitive
            │       │  Use Secret             │  Use ConfigMap
            │       │                         │
```

### When to Use Webhooks vs Built-in

```
┌─────────────────────────────────────────┐
│ Need validation or mutation?           │
└───────────┬─────────────────────────────┘
            ├─ Validation
            │  ┌────────────────────────────────────┐
            │  │ Can be expressed in CEL?           │
            │  └────┬──────────────────────────┬────┘
            │       ├─ Yes (1.26+)             ├─ No
            │       │  ValidatingAdmissionPolicy│  ┌──────────────────────────┐
            │       │  (CEL)                   │  │ Need external data?      │
            │       │                          │  └─┬─────────────────────┬──┘
            │       │                          │    ├─ Yes              ├─ No
            │       │                          │    │  Validating       │  ┌─────────────────┐
            │       │                          │    │  Webhook          │  │ OpenAPI schema? │
            │       │                          │    │                   │  └─┬───────────┬───┘
            │       │                          │    │                   │    ├─ Yes      ├─ No
            │       │                          │    │                   │    │ CRD       │  CEL
            │       │                          │    │                   │    │ schema    │  or
            │       │                          │    │                   │    │           │  Webhook
            ├─ Mutation
            │  ┌────────────────────────────────────┐
            │  │ Can use CRD defaulting?            │
            │  └────┬──────────────────────────┬────┘
            │       ├─ Yes                     ├─ No
            │       │  Use CRD default         │  Mutating
            │       │                          │  Webhook
```

## Deprecated and Removed Features

### Removed (Do Not Use)

| Feature | Removed In | Replacement |
|---------|------------|-------------|
| **PodSecurityPolicy** | 1.25 | Pod Security Admission, OPA |
| **Dockershim** | 1.24 | containerd, CRI-O |
| **In-tree cloud providers** | 1.29+ | Out-of-tree cloud providers |
| **In-tree volume plugins** | 1.29+ | CSI drivers |
| **PodPresets** | 1.20 | Mutating webhooks |
| **Initializers** | 1.14 | Admission webhooks |

### Deprecated (Avoid)

| Feature | Deprecated | Status | Replacement |
|---------|------------|--------|-------------|
| **ABAC** | 1.19 | Maintenance | RBAC |
| **Service Account token secrets** | 1.22 | Retiring | Bound service account tokens |
| **Scheduler Extenders** | 1.23 | Maintenance | Scheduler Framework |
| **kubectl run generators** | 1.18 | Removed | kubectl create |

### Migration Guides

**PodSecurityPolicy → Pod Security Admission:**

```yaml
# ❌ OLD: PodSecurityPolicy (removed in 1.25)
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  # ... many fields

# ✅ NEW: Pod Security Admission (1.22+)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

**In-tree Volume → CSI:**

```yaml
# ❌ OLD: In-tree AWS EBS
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-example
spec:
  capacity:
    storage: 100Gi
  awsElasticBlockStore:  # ❌ Deprecated
    volumeID: vol-12345
    fsType: ext4

# ✅ NEW: CSI
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-example
spec:
  capacity:
    storage: 100Gi
  csi:  # ✅ Use CSI
    driver: ebs.csi.aws.com
    volumeHandle: vol-12345
    fsType: ext4
```

## Summary: Quick Reference

### API Extensions
- ✅ **Use CRDs** for most custom resources
- ✅ **Use API Aggregation** only for custom storage/semantics
- ✅ **Use ConfigMaps/Secrets** for configuration

### Admission Control
- ✅ **Use ValidatingAdmissionPolicy (CEL)** for simple validation (1.26+)
- ✅ **Use Pod Security Admission** for pod security
- ✅ **Use Webhooks** only when CEL insufficient
- ❌ **Avoid PodSecurityPolicy** (removed in 1.25)

### Scheduling
- ✅ **Use Scheduler Framework Plugins** for performance
- ⚠️ **Use Scheduler Extenders** only if necessary (deprecated)
- ✅ **Use Custom Schedulers** for specialized workloads

### Storage
- ✅ **Use CSI** for all storage providers
- ❌ **Avoid in-tree plugins** (deprecated)

### Networking
- ✅ **Use CNI plugins** (Calico, Cilium recommended)
- ✅ **Use Network Policies** for security

### Auth
- ✅ **Use OIDC** for human users
- ✅ **Use RBAC** for authorization
- ✅ **Use ServiceAccount tokens** for pods
- ❌ **Avoid ABAC** (deprecated)

### Compute
- ✅ **Use Device Plugins** for hardware (current)
- ⏳ **Watch DRA** for future (alpha/beta)

## References

### Official Documentation
- [Kubernetes API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
- [API Changes Guidelines](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api_changes.md)
- [Extending Kubernetes](https://kubernetes.io/docs/concepts/extend-kubernetes/)

### KEPs (Kubernetes Enhancement Proposals)
- [KEP-1111: CRD Versioning](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/1111-crd-versioning)
- [KEP-2579: Pod Security Admission](https://github.com/kubernetes/enhancements/tree/master/keps/sig-auth/2579-psp-replacement)
- [KEP-3063: Dynamic Resource Allocation](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/3063-dynamic-resource-allocation)

### SIG References
- API Machinery SIG: API extensions, admission control
- Auth SIG: Authentication, authorization, secrets
- Node SIG: Kubelet, device plugins, DRA
- Scheduling SIG: Scheduler, plugins, extenders
- Storage SIG: CSI, volumes, snapshots
- Network SIG: CNI, network policies, services
