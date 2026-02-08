## Cross-Pod Authentication and Authorization
```mermaid
sequenceDiagram
    %% Participants:
    %% PS - Physical Server
    %% PVS - Provisioning Server (HTTPS Boot)
    %% TPM - Trusted Platform Module
    %% PKI - Public Key Infrastructure
    %% AS - Attestation Service
    %% SPIRE - Secure Production Identity Framework for Everyone (SPIRE Server)
    %% CMS - Configuration Management Server
    %% KCP - Kubernetes Control Plane
    %% CR - Container Registry
    %% SA - SPIRE Agent
    %% WA - Workload A (Pod)
    %% WB - Workload B (Pod)

    participant PS as "Physical Server"
    participant PVS as "Provisioning Server (HTTPS Boot)"
    participant TPM as "Trusted Platform Module"
    participant PKI as "Public Key Infrastructure"
    participant AS as "Attestation Service"
    participant SPIRE as "SPIRE Server"
    participant CMS as "Configuration Management Server"
    participant KCP as "Kubernetes Control Plane"
    participant CR as "Container Registry"
    participant SA as "SPIRE Agent"
    participant WA as "Workload A (Pod)"
    participant WB as "Workload B (Pod)"

    note over PKI: Generate and manage root and intermediate CA certificates
    note over PS: Power on with UEFI Secure Boot enabled
    PS->>PVS: DHCP Discover with UEFI HTTPS Boot options
    PVS->>PS: DHCP Offer with HTTPS Boot URL and certificates signed by Public Key Infrastructure
    PS->>PS: Validate Provisioning Server certificate against trusted CA from Public Key Infrastructure
    PS->>PVS: Establish HTTPS connection using TLS
    PS->>PVS: Download signed bootloader via HTTPS
    PS->>TPM: Verify bootloader signature using Public Key Infrastructure-provisioned keys
    TPM-->>PS: Bootloader signature verified
    PS->>PVS: Download signed OS installer via HTTPS
    PS->>TPM: Verify OS installer signature using Public Key Infrastructure-provisioned keys
    TPM-->>PS: OS installer signature verified
    PS->>TPM: Generate device-specific keys (Endorsement Key, Attestation Identity Key)
    PS->>PKI: Enroll and request device certificates
    PKI-->>PS: Issue device certificates signed by Certificate Authority
    PS->>PS: Store certificates and keys securely in Trusted Platform Module
    PS->>PS: Automated OS installation with encrypted storage
    PS->>TPM: Measure and store boot components
    PS->>AS: Send boot measurements and device certificates for remote attestation
    AS->>PKI: Validate device certificates
    PKI-->>AS: Certificate validation successful
    AS-->>PS: Boot integrity and identity verified
    note over PS: Install and configure Secure Production Identity Framework for Everyone Workload API
    PS->>SPIRE: Request node attestation and registration using device certificates
    SPIRE->>PKI: Verify device certificates and identity
    PKI-->>SPIRE: Certificate validation successful
    SPIRE-->>PS: Issue SPIFFE Verifiable Identity Document (SVID)
    PS->>PS: Access SPIFFE Verifiable Identity Document via Secure Production Identity Framework for Everyone Workload API
    PS->>CMS: Register securely using SPIFFE Verifiable Identity Document and device certificates for authentication
    CMS->>PS: Apply configurations over encrypted channel
    note over PS: Securely install Kubernetes components
    PS->>CR: Pull signed Kubernetes binaries and container images
    PS->>TPM: Verify signatures of Kubernetes binaries and images
    TPM-->>PS: Signatures verified
    PS->>PS: Install kubelet, kubeadm, and kubectl
    PS->>KCP: Request to join Kubernetes cluster using SPIFFE Verifiable Identity Document and device certificates
    KCP->>PKI: Validate Physical Server identity and certificates
    PKI-->>KCP: Certificate validation successful
    KCP-->>PS: Provide cluster certificates and configuration
    PS->>PS: Configure kubelet with cluster certificates and SPIFFE Verifiable Identity Document
    PS->>KCP: Establish mutual TLS connection using SPIFFE identities
    KCP-->>PS: Node successfully joined to cluster
    PS->>PS: Node ready to schedule workloads securely
    note over PS,KCP: Use SPIFFE identities for pod and service authentication

    %% New additions for workload authentication sequence
    note over WA: Workload A (Pod) scheduled on Physical Server
    KCP-->>PS: Schedule Workload A
    PS->>SA: Start Workload A
    WA->>SA: Request SPIFFE Verifiable Identity Document via Secure Production Identity Framework for Everyone Workload API
    SA->>SPIRE: Request workload attestation for Workload A
    SPIRE->>SA: Issue SPIFFE Verifiable Identity Document for Workload A
    SA-->>WA: Provide SPIFFE Verifiable Identity Document to Workload A
    note over WA: Workload A uses SPIFFE Verifiable Identity Document for authentication
    WA->>WB: Initiate secure communication using SPIFFE Verifiable Identity Document
    WB->>WB: Verify Workload A's SPIFFE Verifiable Identity Document via Secure Production Identity Framework for Everyone
    WB-->>WA: Secure communication established
```