## Kubernetes Logical Design

```mermaid
graph TB
    Cluster["Kubernetes Cluster"]

    subgraph Host1["Host 1"]
        Node1["Node 1"]
    end

    subgraph Host2["Host 2"]
        Node2["Node 2"]
    end

    Cluster --> Host1
    Cluster --> Host2

    Node1 --> Pod1["Pod A"]
    Node1 --> Pod2["Pod B"]

    Node2 --> Pod3["Pod C"]
    Node2 --> Pod4["Pod D"]

    Pod1 --> Container1["Container A1"]
    Pod1 --> Container2["Container A2"]

    Pod2 --> Container3["Container B1"]

    Pod3 --> Container4["Container C1"]
    Pod4 --> Container5["Container D1"]

    %% Additional Kubernetes Objects
    Deployment1["Deployment X"]
    ReplicaSet1["ReplicaSet X"]
    Service1["Service Y"]

    Deployment1 --> ReplicaSet1
    ReplicaSet1 --> Pod1
    ReplicaSet1 --> Pod2
    Service1 --> Pod1
    Service1 --> Pod3
```

## Kubernetes Cluster

```mermaid
graph TD
    subgraph ControlPlane["Control Plane"]
        API_Server["kube-apiserver"]
        etcd["etcd"]
        Scheduler["kube-scheduler"]
        Controller_Manager["kube-controller-manager"]
        Cloud_Controller_Manager["cloud-controller-manager"]
    end

    subgraph Cluster["Kubernetes Cluster"]
        ControlPlane
        subgraph Node1["Worker Node 1"]
            Kubelet1["kubelet"]
            KubeProxy1["kube-proxy"]
            Container_Runtime1["Container Runtime"]
            Pod1["Pod A"]
            Pod1 --> ContainerA1["Container A1"]
        end
        subgraph Node2["Worker Node 2"]
            Kubelet2["kubelet"]
            KubeProxy2["kube-proxy"]
            Container_Runtime2["Container Runtime"]
            Pod2["Pod B"]
            Pod2 --> ContainerB1["Container B1"]
        end
    end

    %% Control Plane communicates with Worker Nodes via API Server
    ControlPlane --> API_Server
    API_Server --> Kubelet1
    API_Server --> Kubelet2

    %% Worker Nodes communicate back to Control Plane
    Kubelet1 --> API_Server
    Kubelet2 --> API_Server

    %% Worker Nodes manage their own Pods and Containers
    Kubelet1 --> Pod1
    Kubelet2 --> Pod2
```
```
+---------------------------------+
|      Kubernetes Cluster         |
|                                 |
|  +---------------------------+  |
|  |      Control Plane        |  |
|  |                           |  |
|  |     kube-apiserver        |  |
|  |           etcd            |  |
|  |     kube-scheduler        |  |
|  | kube-controller-manager   |  |
|  | cloud-controller-manager  |  |
|  +-----------+---------------+  |
|               |                 |
|               |                 |
|  +-----------v---------------+  |
|  |        Worker Node 1      |  |
|  |                           |  |
|  |          kubelet          |  |
|  |         kube-proxy        |  |
|  |    Container Runtime      |  |
|  |    +-----------------+    |  |
|  |    |      Pod A      |    |  |
|  |    |  Container A1   |    |  |
|  |    |  Container A2   |    |  |
|  |    +-----------------+    |  |
|  +-----------+---------------+  |
|               |                 |
|  +-----------v---------------+  |
|  |        Worker Node 2      |  |
|  |                           |  |
|  |          kubelet          |  |
|  |         kube-proxy        |  |
|  |    Container Runtime      |  |
|  |    +-----------------+    |  |
|  |    |      Pod B      |    |  |
|  |    |  Container B1   |    |  |
|  |    +-----------------+    |  |
|  +---------------------------+  |
|                                 |
+---------------------------------+
```

# Kubernetes Architecture
```mermaid
graph TB
    %% Control Plane
    subgraph Control_Plane["Control Plane"]
        APIServer["kube-apiserver"]
        etcd["etcd"]
        Scheduler["kube-scheduler"]
        ControllerManager["kube-controller-manager"]
        CloudControllerManager["cloud-controller-manager"]
    end

    %% Worker Nodes
    subgraph Worker_Nodes["Worker Nodes"]
        Node1["Node 1"]
        Node2["Node 2"]

        subgraph Node1_Components["Node 1 Components"]
            Kubelet1["kubelet"]
            KubeProxy1["kube-proxy"]
            ContainerRuntime1["Container Runtime"]
            PodA["Pod A"]
            PodA --> ContainerA1["Container A1"]
            PodA --> ContainerA2["Container A2"]
        end

        subgraph Node2_Components["Node 2 Components"]
            Kubelet2["kubelet"]
            KubeProxy2["kube-proxy"]
            ContainerRuntime2["Container Runtime"]
            PodB["Pod B"]
            PodB --> ContainerB1["Container B1"]
        end
    end

    %% Interactions
    Control_Plane --> APIServer
    APIServer --> etcd
    APIServer --> Scheduler
    APIServer --> ControllerManager
    APIServer --> CloudControllerManager

    APIServer --> Kubelet1
    APIServer --> Kubelet2

    Kubelet1 --> PodA
    Kubelet2 --> PodB

    KubeProxy1 --> PodA
    KubeProxy2 --> PodB

    ContainerRuntime1 --> ContainerA1
    ContainerRuntime1 --> ContainerA2
    ContainerRuntime2 --> ContainerB1
v
    %% Additional Components
    Service["Service"]
    IngressController["Ingress Controller"]
    Storage["Storage"]

    Service --> PodA
    Service --> PodB
    IngressController --> Service
    PodA --> Storage
    PodB --> Storage
```

## Control Plane vs Worker Nodes
---
| Aspect                  | Control Plane                                               | Worker Nodes                                          |
|-------------------------|-------------------------------------------------------------|-------------------------------------------------------|
| **Purpose**             | Manages and orchestrates the cluster                        | Runs containerized applications                       |
| **Components**          | kube-apiserver, etcd, scheduler, etc.                       | kubelet, kube-proxy, container runtime                |
| **Deployment**          | Often on dedicated machines or managed by cloud services    | Deployed across multiple machines/VMs                 |
| **State Management**    | Maintains cluster state via etcd                            | Manages Pod and container states                      |
| **Communication**       | Interfaces with Worker Nodes via API Server                 | Communicates with Control Plane via kube-apiserver    |
| **Scalability**         | Scales independently, often highly available                | Scales based on application needs                     |
| **Security**            | Highly secured, access controlled                           | Secured through node-level policies                   |
| **Resource Allocation** | Cluster-wide resources                                      | Node-specific resources                               |
---
