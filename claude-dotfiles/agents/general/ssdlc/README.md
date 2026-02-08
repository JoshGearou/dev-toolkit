# SSDLC Agents

Secure Software Development Lifecycle agents for security-critical systems.

## Overview

These agents implement security gates throughout the development lifecycle, targeting zero-trust architecture and compliance (GDPR, CCPA, SOC2).

## Agents

| Agent | Type | Purpose |
|-------|------|---------|
| [security-reviewer](security-reviewer.md) | Reviewer | Comprehensive security review across 8 domains |
| [security-writer](security-writer.md) | Writer | Creates threat models, security designs, requirements |
| [threat-model-reviewer](threat-model-reviewer.md) | Reviewer | Reviews code against existing threat models |

## Security Reviewer Domains

The consolidated security-reviewer covers:

| Domain | Focus |
|--------|-------|
| **Authorization** | RBAC/ABAC patterns, IDOR vulnerabilities |
| **Secrets** | Hardcoded credentials, secret manager usage |
| **Privacy** | PII handling, GDPR/CCPA compliance |
| **Blast Radius** | Breach impact, isolation boundaries |
| **Telemetry** | Security logging, audit trails |
| **Threat Models** | STRIDE analysis completeness |
| **Designs** | Security design implementation |
| **Requirements** | Security requirements coverage |

## Security Writer Outputs

Creates security documentation:

- **Threat Models** - STRIDE-based analysis
- **Security Designs** - Implementation specifications
- **Security Requirements** - FR/NFR with acceptance criteria

## STRIDE Threat Modeling

| Threat | Question | Mitigations |
|--------|----------|-------------|
| **Spoofing** | Can attacker impersonate? | Strong auth, MFA |
| **Tampering** | Can data be modified? | Encryption, integrity |
| **Repudiation** | Can actions be denied? | Audit logging |
| **Info Disclosure** | Can data leak? | Authorization |
| **Denial of Service** | Can resources exhaust? | Rate limiting |
| **Elevation** | Can permissions escalate? | Least privilege |

## Security Gates

| Gate | Agent | Purpose |
|------|-------|---------|
| **Pre-Commit** | security-reviewer | Secret scan |
| **PR Creation** | security-reviewer | Full security review |
| **Design Review** | threat-model-reviewer | Threat model validation |
| **Pre-Merge** | All findings addressed | Security sign-off |

## Usage by PR Type

### New External API
```
1. security-writer (create threat model)
2. security-reviewer (full review)
3. threat-model-reviewer (validate implementation)
```

### Auth/AuthZ Change
```
1. security-reviewer (focus: authorization, blast-radius)
2. threat-model-reviewer (validate against model)
```

### New Data Storage
```
1. security-reviewer (focus: privacy, secrets, authorization)
```

## Compliance Mapping

| Standard | Domains |
|----------|---------|
| **GDPR** | Privacy, Secrets, Telemetry |
| **CCPA** | Privacy, Authorization |
| **SOC 2** | Authorization, Secrets, Telemetry |

## Related

- See [code/](../code/) for general code review
- See [docs/](../docs/) for documentation
- See [meta/guides/](../meta/guides/) for agent creation
