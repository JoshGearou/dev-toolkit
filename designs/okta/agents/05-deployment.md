# Okta AD Agents: Deployment

## Network Requirements

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Agent | Okta tenant (*.okta.com) | 443 | HTTPS | Primary communication |
| Agent | Domain Controllers | 389/636 | LDAP/LDAPS | Directory queries |
| Agent | Domain Controllers | 88 | Kerberos | Authentication |
| Agent | Domain Controllers | 3268/3269 | GC | Global Catalog queries |

## Server Sizing

**Okta Official Requirements:**

| Specification | Requirement | Source |
|---------------|-------------|--------|
| Minimum CPU | 2 cores | Okta documentation |
| Minimum RAM | 8 GB | Okta documentation |
| AD Service Account | 20 MB reserved | Okta documentation |
| OS | Windows Server 2016, 2019, 2022, or 2025 | Okta documentation |
| .NET Framework | 4.6.2 or later | Okta documentation |

**Agent Count by User Population:**

| User Count | Minimum Agents | Notes |
|------------|----------------|-------|
| < 30,000 | 2 | Minimum for HA/redundancy |
| > 30,000 | 3 | Okta-documented threshold |
| 50,000+ | 3-4 | Scale based on auth volume |
| 100,000+ | 4+ | Consult Okta; consider geographic distribution |

**Reference:** [Active Directory integration prerequisites | Okta](https://help.okta.com/en-us/content/topics/directory/ad-agent-prerequisites.htm)

## Agent Runtime Configuration

The AD Agent exposes runtime settings via a configuration file that can be tuned for performance, debugging, and network requirements.

**Configuration File Location:**
```
C:\Program Files (x86)\Okta\Okta AD Agent\OktaAgentService.exe.config
```

### Configuration Variables

| Variable | Purpose | Default | Notes |
|----------|---------|---------|-------|
| **PollingThreads** | Concurrent auth request threads | 2 | Max 10; increase for high volume |
| **ConnectionLimit** | Max concurrent connections | 2 | .NET default |
| **DelAuthPostTimeout** | Delegated auth timeout (ms) | 5,000 | Minimum value; increase for slow DCs |
| **MaxRetryLimitSleep** | Retry interval on disconnect (ms) | 3,600,000 | 1 hour default |
| **VerboseLogging** | Enhanced debug logging | False | Enable for troubleshooting |
| **SslPinningEnabled** | SSL certificate verification | False | True in Early Access |
| **ProxyURI** | Proxy server URL:port | None | For outbound connectivity |
| **ProxyUsername** | Proxy auth username | None | — |
| **ProxyPassword** | Proxy auth password (encrypted) | None | — |

**Do not modify:** `AgentKey`, `AgentId`, `AppId`, `ClientId` — these are set during registration. Changing them requires agent re-registration.

### How to Modify Configuration

```powershell
# 1. Stop the service
Stop-Service "OktaADAgent"

# 2. Edit config file
notepad "C:\Program Files (x86)\Okta\Okta AD Agent\OktaAgentService.exe.config"

# 3. Restart the service
Start-Service "OktaADAgent"
```

### Common Tuning Scenarios

| Scenario | Setting | Recommended Change |
|----------|---------|-------------------|
| High auth volume (>10 auth/sec) | `PollingThreads` | Increase to 5-10 |
| Slow DC response times | `DelAuthPostTimeout` | Increase to 10,000+ ms |
| Debugging connectivity issues | `VerboseLogging` | Set to `True` |
| Corporate proxy required | `ProxyURI` | Set to `http://proxy:port` |
| Frequent disconnections | `MaxRetryLimitSleep` | Decrease for faster retry |

### Thread Configuration

| Setting | Default | Maximum | Notes |
|---------|---------|---------|-------|
| Worker threads (`PollingThreads`) | 2 | 10 | Increase for high auth volume |
| Reserved thread | 1 | 1 | Always reserved for auth tasks |

Okta randomly distributes authentication jobs across available agents in the pool.

**Reference:** [Okta AD Agent Variable Definitions](https://help.okta.com/en-us/content/topics/directory/ad-agent-appsettings.htm)

## Performance Considerations

**Important:** Okta does not publish specific QPS (queries per second) benchmarks for AD Agent delegated authentication. Performance depends on:

- Network latency between agent and Okta cloud
- Network latency between agent and Domain Controllers
- Domain Controller response time
- Number of configured threads
- Concurrent authentication load

**RADIUS Agent Benchmark (Similar Architecture):**

For reference, Okta's RADIUS agent (which uses similar outbound architecture) achieved:

| Metric | Value | Test Environment |
|--------|-------|------------------|
| Auth rate | ~6.5/second | AWS t2.medium (2 vCPU, 4 GB) |
| Throughput | ~390/minute | 15 worker threads |
| CPU utilization | 3% | Under load |
| Error rate | 0% | Okta Verify Push + Security Question |

**Reference:** [RADIUS throughput and scaling benchmarks | Okta](https://help.okta.com/en-us/content/topics/integrations/radius-best-pract-thruput.htm)

AD Agent delegated authentication involves additional LDAP operations to AD, so actual throughput may differ. Organizations should **benchmark in their own environment** before production deployment.

## Capacity Planning

### Understanding Authentication Load

Authentication load is not uniformly distributed. Large enterprises typically see:

| Time Period | Relative Load | Driver |
|-------------|---------------|--------|
| Morning peak (8-10 AM local) | 5-10x baseline | Workday start, session refreshes |
| Lunch dip (12-1 PM) | 0.5x baseline | Reduced activity |
| Afternoon steady (2-5 PM) | 1-2x baseline | Normal operations |
| Evening/weekend | 0.1x baseline | Minimal activity |
| Incident response | 10-20x baseline | Mass password reset, security event |

### Capacity Planning Formula

Use this formula to estimate required agents:

```
Required Agents = ceiling(
    (Peak Auth Rate × Safety Factor) / (Per-Agent Throughput × Thread Count)
) + HA Buffer

Where:
- Peak Auth Rate = Expected authentications per second at peak
- Safety Factor = 1.5 (50% headroom for spikes)
- Per-Agent Throughput = ~3-5 auths/sec/thread (conservative estimate for delegated auth)
- Thread Count = Configured threads per agent (default 2, max 10)
- HA Buffer = +1 minimum (to survive single agent failure)
```

### Worked Examples

#### Example 1: Mid-size Enterprise

**Scenario:** 50,000 employees, standard 9-5 workforce, North America only

**Step 1: Estimate peak auth rate**
```
Daily active users: 50,000 × 90% = 45,000
Logins per user per day: 3 (morning, after lunch, session refresh)
Total daily auths: 45,000 × 3 = 135,000
Peak hour auths: 135,000 × 0.4 = 54,000 (40% of logins in peak 2 hours)
Peak auth rate: 54,000 / 7,200 sec = 7.5 auths/sec
```

**Step 2: Calculate agents**
```
Per-agent capacity: 4 auths/sec/thread × 5 threads = 20 auths/sec
Required capacity: 7.5 auths/sec × 1.5 safety = 11.25 auths/sec
Base agents: ceiling(11.25 / 20) = 1 agent
With HA buffer: 1 + 1 = 2 agents
```

**Recommendation:** 2 agents (Okta minimum), 5 threads each

---

#### Example 2: Large Enterprise

**Scenario:** 150,000 employees, 24/7 operations, 3 global regions

**Step 1: Estimate peak auth rate**
```
Daily active users: 150,000 × 85% = 127,500
Logins per user per day: 4 (MFA challenges, session refreshes)
Total daily auths: 127,500 × 4 = 510,000
Peak hour auths (per region): 510,000 / 3 regions × 0.35 = 59,500
Peak auth rate per region: 59,500 / 3,600 sec = 16.5 auths/sec
Global concurrent peak: 16.5 × 2 = 33 auths/sec (overlap)
```

**Step 2: Calculate agents per region**
```
Per-agent capacity: 4 auths/sec/thread × 8 threads = 32 auths/sec
Required capacity: 16.5 auths/sec × 1.5 safety = 24.75 auths/sec
Base agents: ceiling(24.75 / 32) = 1 agent
With HA buffer: 1 + 2 = 3 agents (critical system)
```

**Recommendation:** 3 agents per region (9 total), 8 threads each

---

#### Example 3: Very Large Enterprise with Complex AD

**Scenario:** 300,000 employees, complex AD (50,000 groups, deep nesting)

**Step 1: Adjust for AD complexity**
```
Base auth time: 150ms (simple AD)
Group lookup overhead: +100ms per 3 nesting levels
Attribute fetch overhead: +50ms for extended attributes
Adjusted auth time: 150 + 100 + 50 = 300ms
Effective throughput reduction: 50% of baseline
```

**Step 2: Recalculate capacity**
```
Per-agent capacity: 4 auths/sec × 0.5 (complexity factor) × 10 threads = 20 auths/sec
Peak auth rate: 60 auths/sec (estimated)
Required capacity: 60 × 1.5 = 90 auths/sec
Base agents: ceiling(90 / 20) = 5 agents
With HA buffer: 5 + 2 = 7 agents
```

**Recommendation:** 7 agents, 10 threads each, consider OU sharding

### Sync Capacity Planning

Sync operations have different capacity characteristics than authentication:

| Sync Type | Characteristics | Duration Estimate |
|-----------|-----------------|-------------------|
| Full Initial Sync | Bulk LDAP queries, high network I/O | 50,000 users ≈ 1-2 hours |
| Incremental Sync | USN-based delta queries | 1,000 changes ≈ 5-10 min |
| Group Sync | Recursive membership resolution | Varies greatly with nesting |

**Full Sync Duration Formula:**
```
Duration (hours) = (Users × (1 + Groups/Users × Group_Factor)) / Sync_Rate

Where:
- Sync_Rate ≈ 10,000-20,000 objects/hour (typical)
- Group_Factor = 0.5 (flat) to 5.0 (deep nesting)
```

**Example: 100,000 users, 30,000 groups, moderate nesting**
```
Duration = (100,000 × (1 + 30,000/100,000 × 2.0)) / 15,000
Duration = (100,000 × 1.6) / 15,000
Duration = 10.7 hours
```

**Implication:** Schedule full syncs during low-activity periods; expect 10+ hour windows for large environments.

### Stress Testing Recommendations

Before production deployment at scale, validate capacity:

| Test Type | How to Execute | Success Criteria |
|-----------|----------------|------------------|
| **Baseline Auth** | 10 concurrent users, measure latency | p99 < 500ms |
| **Load Test** | Ramp to 2x expected peak | No errors, p99 < 1s |
| **Soak Test** | Sustained 1x peak for 4 hours | No memory leaks, stable latency |
| **Failover Test** | Kill 1 agent during load | No user-visible errors |
| **Full Sync Under Load** | Run sync during auth peak | Auth latency increase < 50% |

### Capacity Planning Decision Tree

```
Start: Estimate peak auth rate
    │
    ▼
Is rate < 10 auth/sec?
    ├── Yes → 2 agents (minimum HA), 5 threads each
    │
    └── No → Calculate: rate × 1.5 / 20 auths/agent = base count
              │
              ▼
         Is AD complex (>10K groups or deep nesting)?
              ├── Yes → Multiply base count × 1.5
              │
              └── No → Use base count
                        │
                        ▼
                   Add HA buffer:
                   - Standard: +1 agent
                   - Critical: +2 agents
                   - Compliance: +3 agents (survive AZ failure)
                        │
                        ▼
                   Is user base > 100K?
                        ├── Yes → Consider OU sharding into multiple integrations
                        │
                        └── No → Single integration sufficient
```

## Version Consistency

**Critical:** If running multiple AD agents, all agents must be the same version. Mismatched versions cause all agents in that domain to function at the level of the oldest agent.

## Installation Process

### AD Agent Installation

1. In Okta Admin Console, go to **Directory > Directory Integrations**
2. Click **Add Active Directory**
3. Download the agent installer (contains registration token)
4. Run installer on Windows Server (domain-joined)
5. Agent registers with Okta using embedded token
6. Configure import scope (OUs, groups, filters)
7. Run initial import

### Password Sync Agent Installation

1. Download Password Sync Agent from Okta Admin Console
2. Install on **every writable Domain Controller**
3. Agent registers with Okta
4. Password Filter DLL captures password changes
5. Verify sync by changing a test user's password

### IWA Agent Installation

1. Download IWA Agent from Okta Admin Console
2. Install on Windows Server (domain-joined)
3. Register SPN (Service Principal Name) for agent
4. Configure DNS for IWA endpoint
5. Configure browser settings for Kerberos/NTLM
6. Test with domain-joined workstation

## Upgrade Process

1. Download new agent version from Okta Admin Console
2. Stop agent service on one server
3. Run installer (preserves configuration)
4. Verify agent reconnects and is healthy
5. Repeat for remaining agents

**Important:** Upgrade agents one at a time to maintain availability during the upgrade window.

## Infrastructure as Code (IaC) Support

Okta has mixed support for Infrastructure as Code with AD agents.

### What CAN Be Automated

**Okta Terraform Provider:**

Okta has an official Terraform provider that can manage directory integration **configuration**, but not agent installation:

| Resource Type | Terraform Support |
|---------------|-------------------|
| User provisioning settings | Yes |
| Group assignments | Yes |
| Application assignments | Yes |
| Sign-on policies | Yes |
| Some directory integration settings | Partial |

**Reference:** [Okta Terraform Provider](https://registry.terraform.io/providers/okta/okta/latest/docs)

**Okta APIs:**

| Capability | API Support | Notes |
|------------|-------------|-------|
| List directory integrations | Yes | GET /api/v1/directories |
| Get integration details | Yes | GET /api/v1/directories/{id} |
| Update integration settings | Partial | Some settings only |
| Create integration | No | Must use Admin Console |
| Generate agent registration token | No | Must use Admin Console |
| Install/manage agents | No | Agents are on-prem |

**Agent Installation Automation:**

The agent installation can be automated using standard Windows deployment tools:

| Tool | Approach |
|------|----------|
| **PowerShell** | Silent install with parameters |
| **SCCM/Intune** | Package and deploy MSI |
| **Ansible** | win_package module |
| **Puppet/Chef** | Windows package resources |
| **Group Policy** | Software installation GPO |

**Silent Install Example:**
```powershell
# Download installer from Okta Admin Console first
# Registration token is embedded in the installer

.\OktaADAgentSetup.exe /quiet /norestart
```

### What CANNOT Be Automated

| Capability | Why Not |
|------------|---------|
| Create new directory integration | Requires Admin Console wizard |
| Generate agent registration token | No API endpoint |
| Initial agent-to-Okta binding | Token embedded in downloaded installer |
| Password Sync Agent registration | Requires Admin Console |

### The Registration Token Gap

The main IaC gap is the **registration token**. The workflow requires a manual step:

```
┌─────────────────────────────────────────────────────────────┐
│  MANUAL STEP (Cannot be automated via API)                   │
│                                                              │
│  1. Admin Console → Directory → Add AD                       │
│  2. Download installer (contains unique registration token)  │
│  3. Token is one-time use, expires                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  CAN BE AUTOMATED                                            │
│                                                              │
│  4. Deploy installer via SCCM/Ansible/etc.                  │
│  5. Silent install on target servers                        │
│  6. Agent registers using embedded token                    │
└─────────────────────────────────────────────────────────────┘
```

### IaC Workarounds

**1. Pre-stage Registrations:**
1. Manually create directory integrations in Okta (one-time per environment)
2. Download installers (with tokens) for each environment
3. Store installers in artifact repository
4. Automate deployment from there

**2. Hybrid Approach:**
- Accept the manual step for initial integration setup
- Automate agent deployment using Windows automation tools
- Use Terraform for Okta-side configuration (policies, apps, users)

### Comparison with Azure AD Connect

| Capability | Okta AD Agent | Azure AD Connect |
|------------|---------------|------------------|
| Terraform provider | Partial | Azure provider covers AAD |
| Agent silent install | Yes | Yes |
| Programmatic registration | No | Yes (via Azure CLI/PowerShell) |
| Config as code | Limited | ARM templates, PowerShell |
| API for full lifecycle | No | Yes (Microsoft Graph) |

## Document Navigation

- **Previous:** [04-high-availability.md](04-high-availability.md) - HA and load balancing
- **Next:** [06-large-enterprise.md](06-large-enterprise.md) - Large enterprise patterns
- **Index:** [README.md](../README.md)
