# Workload Authorization Flow with Cedar

## Resource queries PEP directly
```mermaid
sequenceDiagram
    participant Workload
    participant SPIRE_Agent as SPIRE Agent
    participant Resource
    participant PEP as Policy Enforcement Point
    participant PDP as Policy Decision Point (Cedar)

    %% Workload obtains SVID from SPIRE Agent
    Workload->>SPIRE_Agent: FetchX509SVIDRequest()
    SPIRE_Agent-->>Workload: FetchX509SVIDResponse(SVID, Private Key)

    %% Workload sends access request to Resource
    Workload->>Resource: Access Request (SVID, Action, Resource ID)
    note over Workload: Includes identity and request details

    %% Resource forwards request to PEP
    Resource->>PEP: Forward Request
    PEP->>PEP: Extract Identity & Request Details

    %% PEP queries PDP for authorization decision
    PEP->>PDP: Is Workload allowed to perform Action on Resource?
    note right of PDP: Evaluates request using Cedar policies
    PDP-->>PEP: Authorization Decision (Allow/Deny)

    %% PEP enforces decision
    PEP-->>Resource: Authorization Result
    Resource-->>Workload: Access Granted or Access Denied
```

## Resource request is intercepted by proxy or sidecar and queries the PEP
```mermaid
sequenceDiagram
    participant Workload
    participant PEP as Policy Enforcement Point
    participant PDP as Policy Decision Point (Cedar)
    participant Resource

    %% Workload obtains SVID from SPIRE Agent
    Workload->>SPIRE_Agent: FetchX509SVIDRequest()
    SPIRE_Agent-->>Workload: FetchX509SVIDResponse(SVID, Private Key)

    %% Workload sends access request to PEP
    Workload->>PEP: Access Request (SVID, Action, Resource ID)
    note over Workload: Includes identity and request details

    %% PEP extracts identity and request details
    PEP->>PEP: Extract Identity & Request Details

    %% PEP queries PDP for authorization decision
    PEP->>PDP: Is Workload allowed to perform Action on Resource?
    note right of PDP: Evaluates request using Cedar policies
    PDP-->>PEP: Authorization Decision (Allow/Deny)

    alt Allow
        %% PEP forwards request to Resource
        PEP->>Resource: Forwarded Request (Action, Resource ID)
        Resource-->>PEP: Response Data
        %% PEP returns response to Workload
        PEP-->>Workload: Access Granted (Response Data)
    else Deny
        %% PEP denies access
        PEP-->>Workload: Access Denied
    end
```

## Using Attribute Based Access Control with Cedar Policies

```mermaid
sequenceDiagram
    participant Workload
    participant PEP as Policy Enforcement Point
    participant PDP as Policy Decision Point (Cedar)
    participant AttributeStore as Attribute Store
    participant Resource

    %% Workload obtains SVID from SPIRE Agent
    Workload->>SPIRE_Agent: FetchX509SVIDRequest()
    SPIRE_Agent-->>Workload: FetchX509SVIDResponse(SVID, Private Key)

    %% Workload sends access request to PEP
    Workload->>PEP: Access Request (SVID, Action, Resource ID)
    note over Workload: Includes identity and request details

    %% PEP extracts identity and request details
    PEP->>PEP: Extract Identity & Request Details

    %% PEP queries PDP for authorization decision
    PEP->>PDP: Authorization Query (Principal, Action, Resource)
    note right of PDP: Needs attributes for evaluation

    %% PDP retrieves attributes from Attribute Store
    PDP->>AttributeStore: Get Attributes (Principal, Resource)
    AttributeStore-->>PDP: Return Attributes

    %% PDP evaluates policy using Cedar
    PDP->>PDP: Evaluate Policy with Attributes
    PDP-->>PEP: Authorization Decision (Allow/Deny)

    alt Allow
        %% PEP forwards request to Resource
        PEP->>Resource: Forwarded Request (Action, Resource ID)
        Resource-->>PEP: Response Data
        %% PEP returns response to Workload
        PEP-->>Workload: Access Granted (Response Data)
    else Deny
        %% PEP denies access
        PEP-->>Workload: Access Denied
    end
```