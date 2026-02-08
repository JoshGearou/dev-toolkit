# Okta Active Directory Integration

Technical documentation for Okta AD agents and hybrid identity integration.

## Documentation Index

| Document | Description |
|----------|-------------|
| [agents/01-overview.md](agents/01-overview.md) | Executive summary, key terminology, agent types, and **glossary** |
| [agents/02-architecture.md](agents/02-architecture.md) | Outbound connection model, authentication modes, and auth flows |
| [agents/03-agent-types.md](agents/03-agent-types.md) | AD Agent, Password Sync, IWA, LDAP, and RADIUS agents |
| [agents/04-high-availability.md](agents/04-high-availability.md) | HA patterns, load balancing, routing, and failure scenarios |
| [agents/05-deployment.md](agents/05-deployment.md) | Server sizing, network requirements, and installation |
| [agents/06-large-enterprise.md](agents/06-large-enterprise.md) | Multiple integrations, geographic patterns, and scaling |
| [agents/07-security-operations.md](agents/07-security-operations.md) | Security considerations, monitoring, and troubleshooting |

## Quick Reference

**Key Concepts:**
- **Directory Integration**: A configured connection in Okta to an AD domain
- **Delegated Authentication**: Credentials validated against AD in real-time via agents
- **Password Sync**: Password hashes synced to Okta; no agent needed for auth

**Agent Types:**
| Agent | Purpose |
|-------|---------|
| AD Agent | User/group sync, delegated auth |
| Password Sync Agent | Real-time password synchronization |
| IWA Agent | Kerberos-based desktop SSO |
| LDAP Agent | LDAP interface to Okta |
| RADIUS Agent | RADIUS authentication proxy |

**Minimum Production Deployment:**
- 2+ agents per AD domain for HA
- 3+ agents for >30,000 users
- All agents must run the same version

## Related Documents

- [PRR_for_Okta.md](PRR_for_Okta.md) - Product Requirements Review

## References

- [Okta AD Agent Prerequisites](https://help.okta.com/en-us/content/topics/directory/ad-agent-prerequisites.htm)
- [Okta Rate Limits](https://developer.okta.com/docs/reference/rate-limits/)
- [RADIUS Throughput Benchmarks](https://help.okta.com/en-us/content/topics/integrations/radius-best-pract-thruput.htm)
