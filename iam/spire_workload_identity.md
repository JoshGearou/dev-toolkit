# SPIRE Identity Overview

## High-Level System Diagram for SPIRE with Kubernetes Microservices

```mermaid
graph LR
    subgraph Kubernetes Cluster
        subgraph Node1
            Agent1[SPIRE Agent]
            ServiceA[Microservice A]
            Agent1 --> ServiceA
        end
        subgraph Node2
            Agent2[SPIRE Agent]
            ServiceB[Microservice B]
            Agent2 --> ServiceB
        end
    end
    SPIRE_Server[SPIRE Server]
    SPIRE_Server --> Agent1
    SPIRE_Server --> Agent2
    ServiceA -- mTLS Communication --> ServiceB
```

## High-Level UML Sequence Diagram for Establishing a SPIRE Identity

```mermaid
sequenceDiagram
    participant Workload
    participant SPIRE_Agent as SPIRE Agent
    participant SPIRE_Server as SPIRE Server

    Workload->>SPIRE_Agent: Request SVID
    SPIRE_Agent->>SPIRE_Server: Workload Attestation
    SPIRE_Server-->>SPIRE_Agent: Attestation Response
    SPIRE_Agent->>SPIRE_Server: Fetch SVID
    SPIRE_Server-->>SPIRE_Agent: Provide SVID
    SPIRE_Agent->>Workload: Deliver SVID
```
## Detailed UML Sequence Diagram for Establishing a SPIRE Identity

```mermaid
sequenceDiagram
    participant Workload
    participant SPIRE_Agent as SPIRE Agent
    participant SPIRE_Server as SPIRE Server

    Workload->>SPIRE_Agent: Connect to Workload API
    Note over Workload,SPIRE_Agent: Workload Attestation Begins
    SPIRE_Agent->>SPIRE_Agent: Collect Selectors
    SPIRE_Agent->>SPIRE_Server: Send Attestation Data (Selectors)
    SPIRE_Server-->>SPIRE_Agent: Attestation Result (Authorized/Unauthorized)
    alt Authorized
        SPIRE_Agent->>SPIRE_Agent: Generate Key Pair
        SPIRE_Agent->>SPIRE_Server: Submit CSR (Contains Public Key & SPIFFE ID)
        SPIRE_Server-->>SPIRE_Agent: Return SVID (Signed Certificate)
        SPIRE_Agent->>Workload: Provide SVID and Private Key
        Note over Workload: Stores SVID and Key Securely
    else Unauthorized
        SPIRE_Agent-->>Workload: Deny Request
    end
```

## Workload to SPIRE Agent Payload

```mermaid
sequenceDiagram
    participant Workload
    participant SPIRE_Agent as SPIRE Agent
    participant SPIRE_Server as SPIRE Server

    %% Workload initiates SVID request
    Workload->>SPIRE_Agent: FetchX509SVIDRequest()
    note right of Workload: gRPC call over Unix Socket

    %% SPIRE Agent begins attestation
    note over SPIRE_Agent: Workload Attestation Begins
    SPIRE_Agent->>SPIRE_Agent: Collect Selectors (PID, UID, Labels)

    %% SPIRE Agent sends attestation data to SPIRE Server
    SPIRE_Agent->>SPIRE_Server: WorkloadAttestRequest(selectors)
    note right of SPIRE_Agent: Includes collected selectors

    %% SPIRE Server processes attestation
    SPIRE_Server-->>SPIRE_Agent: WorkloadAttestResponse(status, SPIFFE ID)
    alt Authorized
        %% SPIRE Agent generates key pair and CSR
        SPIRE_Agent->>SPIRE_Agent: Generate Key Pair
        SPIRE_Agent->>SPIRE_Server: CSR Request (Public Key, SPIFFE ID)
        %% SPIRE Server issues SVID
        SPIRE_Server-->>SPIRE_Agent: SVID Response (Signed Certificate)
        %% SPIRE Agent returns SVID and key to workload
        SPIRE_Agent->>Workload: FetchX509SVIDResponse(SVID, Private Key)
        note right of Workload: Stores SVID and Key Securely
    else Unauthorized
        %% SPIRE Agent denies request
        SPIRE_Agent-->>Workload: Error Response (Permission Denied)
    end
```