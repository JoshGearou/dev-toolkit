# Okta AD Agents: Overview

## Executive Summary

Okta Active Directory (AD) agents enable hybrid identity integration between on-premises Active Directory infrastructure and Okta's cloud identity platform. These lightweight Windows services establish secure outbound-only connections, allowing organizations to leverage cloud identity capabilities while maintaining sensitive authentication operations within their network perimeter.

## Key Terminology

| Term | Definition |
|------|------------|
| **Directory Integration** | A configured connection in Okta to an external directory (AD domain). Found in Admin Console under Directory → Directory Integrations. |
| **AD Agent** | Windows service that handles user sync and delegated authentication for a directory integration. |
| **Agent Registration** | Process of binding an agent to a specific directory integration using a registration token. |
| **Delegated Authentication** | Authentication mode where credentials are validated against AD in real-time via agents. |
| **Password Sync** | Authentication mode where password hashes sync to Okta; agents not required for authentication. |

**Important:** Each agent registers to exactly one directory integration. You can create multiple directory integrations for the same AD domain with different OU scopes.

## Agent Types and Capabilities

Okta provides several specialized agents for different integration scenarios:

| Agent Type | Primary Function | Deployment Location |
|------------|------------------|---------------------|
| AD Agent | User/group sync, delegated authentication | Domain-joined server |
| Password Sync Agent | Real-time password synchronization | Every writable Domain Controller |
| IWA Agent | Kerberos-based desktop SSO | Domain-joined server |
| LDAP Agent | LDAP interface to Okta Universal Directory | Application-accessible server |
| RADIUS Agent | RADIUS authentication proxy | Network-accessible server |

## Glossary

Comprehensive terminology reference for Okta AD integration.

### A

| Term | Definition |
|------|------------|
| **AD Agent** | Windows service installed on a domain-joined server that handles user/group synchronization and delegated authentication between Active Directory and Okta. |
| **Agent Gateway** | Okta cloud component that terminates persistent connections from on-premises agents and routes authentication requests. |
| **Agent Pool** | Informal term for the set of agents registered to a single directory integration. Okta load balances across all healthy agents in the pool. |
| **Agent Registration Token** | One-time-use token embedded in the agent installer that binds the agent to a specific directory integration during installation. Cannot be generated via API. |
| **Attribute Mapping** | Configuration that defines how AD attributes (e.g., `sAMAccountName`, `mail`) map to Okta profile attributes. |

### B

| Term | Definition |
|------|------------|
| **Blast Radius** | The scope of impact when a component fails. For agents, this is the set of users whose authentication depends on that agent or integration. |
| **Bind (LDAP)** | The LDAP operation that authenticates a connection. Delegated auth uses two binds: service account bind (for user lookup) and user bind (for credential validation). |

### C

| Term | Definition |
|------|------------|
| **Connection Persistence** | The mechanism by which agents maintain long-lived outbound connections (WebSocket or HTTP long-polling) to Okta's gateway, enabling the cloud to push requests to on-premises infrastructure. |
| **Credential Cache** | With delegated authentication, Okta caches a hash of credentials for **5 days** after successful login. If agents are unavailable, users with valid cached credentials can still authenticate. Users who never logged in or whose cache expired cannot authenticate during an outage. See [Okta docs](https://support.okta.com/help/s/article/Cache-AD-Credentials-using-Delegated-Authentication). |

### D

| Term | Definition |
|------|------------|
| **Delegated Authentication** | Authentication mode where user credentials are validated against Active Directory in real-time via agents. Passwords never leave the corporate network. |
| **Directory Integration** | A configured connection in Okta Admin Console (Directory → Directory Integrations) to an external directory such as an AD domain. Each integration has its own agents, OU scope, and sync settings. |
| **Domain Controller (DC)** | Windows server running Active Directory Domain Services. Agents query DCs for user information and credential validation. |
| **DynamicScale** | Okta add-on that increases API rate limits for high-volume enterprise deployments. Requires additional licensing. |

### F

| Term | Definition |
|------|------------|
| **Full Sync** | Import operation that reads all users and groups within the configured scope from AD. Typically scheduled weekly for large environments. |

### G

| Term | Definition |
|------|------------|
| **Global Catalog (GC)** | AD service (ports 3268/3269) that provides read access to objects across all domains in a forest. Used for cross-domain queries. |
| **gMSA (Group Managed Service Account)** | AD account type with automatic password management. Recommended for Okta service accounts to eliminate manual password rotation. |

### H

| Term | Definition |
|------|------------|
| **Heartbeat** | Periodic signal from agent to Okta gateway indicating the agent is healthy. Missed heartbeats (typically 30 seconds) result in the agent being marked unhealthy. |
| **HTTP 429** | "Too Many Requests" response code indicating rate limit exceeded. Agents should implement exponential backoff when receiving 429 responses. |

### I

| Term | Definition |
|------|------------|
| **Import** | Okta term for synchronizing users and groups from AD to Okta Universal Directory. Can be full import or incremental import. |
| **Incremental Sync** | Import operation that uses AD's USN (Update Sequence Number) to fetch only objects changed since the last sync. Lower API impact than full sync. |
| **IWA (Integrated Windows Authentication)** | Authentication mechanism using Kerberos or NTLM that enables SSO for domain-joined workstations. Okta IWA Agent provides this capability. |
| **IWA Agent** | Okta agent that provides desktop SSO for domain-joined workstations using Kerberos/NTLM authentication. |

### J

| Term | Definition |
|------|------------|
| **JIT Provisioning (Just-In-Time)** | Creating an Okta user profile automatically during first authentication, rather than waiting for scheduled sync. Part of the delegated auth flow. |

### K

| Term | Definition |
|------|------------|
| **Kerberos** | Network authentication protocol used by AD for single sign-on. IWA Agent uses Kerberos tickets for authentication. |

### L

| Term | Definition |
|------|------------|
| **LDAP (Lightweight Directory Access Protocol)** | Protocol used to query and modify directory services. AD Agents use LDAP (ports 389/636) to communicate with Domain Controllers. |
| **LDAP Agent** | Okta agent that provides an LDAP interface to Okta Universal Directory, enabling legacy applications to authenticate against Okta. |
| **LDAPS** | LDAP over TLS (port 636). Recommended for secure communication between agents and Domain Controllers. |
| **Log Streaming** | Okta feature that sends System Log events to external destinations (Splunk, AWS EventBridge, Datadog) in near real-time. |

### M

| Term | Definition |
|------|------------|
| **MFA (Multi-Factor Authentication)** | Authentication requiring multiple verification factors. Okta evaluates MFA policies after successful primary authentication (delegated or password sync). |

### O

| Term | Definition |
|------|------------|
| **Okta-Mastered** | User accounts that exist only in Okta Universal Directory with no source directory. Used for contractors, partners, and cloud-only users. |
| **Okta FastPass** | Passwordless authentication method using Okta Verify app. Bypasses agents entirely, reducing infrastructure dependency. |
| **Okta Universal Directory (UD)** | Okta's cloud-based user directory that aggregates identities from multiple sources (AD, LDAP, HR systems, Okta-mastered). |
| **OU (Organizational Unit)** | AD container for organizing objects (users, groups, computers). Directory integrations can be scoped to specific OUs. |
| **Outbound-Only** | Agent connection model where all connections are initiated from on-premises to Okta cloud. No inbound firewall rules required. |

### P

| Term | Definition |
|------|------------|
| **Password Filter DLL** | Windows component installed by Password Sync Agent that intercepts password changes on Domain Controllers. |
| **Password Sync Agent (PSA)** | Okta agent installed on every writable Domain Controller that captures password changes and syncs hashes to Okta. |
| **Password Sync** | Authentication mode where password hashes synchronize from AD to Okta, enabling authentication without agent involvement. |
| **Persistent Connection** | Long-lived network connection (WebSocket or HTTP long-polling) maintained by agents to Okta gateway. |
| **Principal** | Identity performing an action. In Okta context, typically a user or service account. |
| **Provisioning** | Creating, updating, or deactivating user accounts. Can be inbound (AD → Okta) or outbound (Okta → AD writeback). |

### R

| Term | Definition |
|------|------------|
| **RADIUS Agent** | Okta agent that provides RADIUS protocol support for network devices (VPNs, wireless controllers) to authenticate against Okta. |
| **Rate Limit** | Okta-imposed restrictions on API request volume. Key limits: 2,000 auth/min, 600 GET/min for Users API. |
| **Registration** | Process of binding an agent to a directory integration using a one-time token from the Admin Console. |

### S

| Term | Definition |
|------|------------|
| **sAMAccountName** | AD attribute containing the pre-Windows 2000 logon name (e.g., `jsmith`). Often used for user lookup. |
| **Service Account** | AD account used by Okta agents for LDAP queries and operations. Should have read access to users/groups in scope. |
| **SIEM (Security Information and Event Management)** | Platform for aggregating and analyzing security logs (e.g., Splunk, Microsoft Sentinel, Datadog). Okta integration via Log Streaming (near real-time) or System Log API (polling). Key use cases: auth anomaly detection, agent health monitoring, compliance reporting. See [07-security-operations.md](07-security-operations.md) for detection rules and queries. |
| **SOAR (Security Orchestration, Automation and Response)** | Platform for automating security incident response (e.g., Splunk SOAR, Palo Alto XSOAR, Tines). Integrates with Okta APIs to automate actions: suspend/unsuspend users, clear sessions, reset passwords, revoke tokens. Enables playbooks for agent-down response, brute force mitigation, and suspicious activity investigation. See [07-security-operations.md](07-security-operations.md) for example playbooks. |
| **SPN (Service Principal Name)** | AD identifier for a service instance. Required for IWA Agent Kerberos configuration. |
| **Sync** | Process of importing users and groups from AD to Okta Universal Directory. See Full Sync, Incremental Sync. |

### T

| Term | Definition |
|------|------------|
| **Thread (Agent)** | Worker thread in AD Agent that handles authentication requests. Default is 2 threads, maximum is 10. |
| **TLS (Transport Layer Security)** | Encryption protocol. All agent-to-Okta communication uses TLS 1.2 or higher. |

### U

| Term | Definition |
|------|------------|
| **Universal Directory (UD)** | See Okta Universal Directory. |
| **UPN (User Principal Name)** | AD attribute in email format (e.g., `jsmith@corp.com`). Primary identifier for user lookup during authentication. |
| **USN (Update Sequence Number)** | AD mechanism for tracking changes. Incremental sync uses USN to identify objects changed since last sync. |

### W

| Term | Definition |
|------|------------|
| **WebSocket** | Protocol for bidirectional communication over a single TCP connection. Used by agents for persistent connection to Okta gateway. |
| **Worker Thread** | See Thread (Agent). |
| **Writeback** | Provisioning from Okta to AD (e.g., creating users in AD when created in Okta). Requires service account with write permissions. |

### Acronym Quick Reference

| Acronym | Expansion |
|---------|-----------|
| AD | Active Directory |
| DC | Domain Controller |
| GC | Global Catalog |
| gMSA | Group Managed Service Account |
| IWA | Integrated Windows Authentication |
| JIT | Just-In-Time |
| LDAP | Lightweight Directory Access Protocol |
| MFA | Multi-Factor Authentication |
| OU | Organizational Unit |
| PSA | Password Sync Agent |
| RADIUS | Remote Authentication Dial-In User Service |
| SIEM | Security Information and Event Management |
| SOAR | Security Orchestration, Automation and Response |
| SPN | Service Principal Name |
| SSO | Single Sign-On |
| TLS | Transport Layer Security |
| UD | Universal Directory |
| UPN | User Principal Name |
| USN | Update Sequence Number |

## Document Navigation

- **Next:** [02-architecture.md](02-architecture.md) - Connection model and authentication flows
- **Index:** [README.md](../README.md)
