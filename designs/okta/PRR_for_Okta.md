# Production Readiness Review

***PLEASE MAKE THE DOCUMENT TO COMMENT instead of Restricted***  
***\<Template: [go/prr/template](https://go/prr/template)\>***

***This document is guidance on how to conduct production readiness reviews for your services. This template is meant to be filled out starting from the beginning of SDLC and completed before a new system is GA’ed. A Sr Staff+ in the area or adjacent area is expected to be an approver. This template should also be used for existing systems to keep their information up to date.***

| System Name | Okta |
| ----: | :---- |
| PRR Version | 1.0 |
| PRR Template Version | 2.2.0 |
| Presenter | [Ramki Mohan](mailto:rmohan@linkedin.com) |
| Internal Reviewers | [Rick Erickson](mailto:rerickson@linkedin.com) : Waiting [Tim Hilliard](mailto:thilliard@linkedin.com) : In review |
| Internal Approver(s) *Who from your team will double check and validate this work?* | [Rick Erickson](mailto:rerickson@linkedin.com) : Not started  |
| External Approver(s) | Person Person |
| Last Revised Date | Nov 20 2025 |

## **Summary**

*What does this system do at a high level (2-3 sentence max summary):*  
*Okta is the Identity Provider for 3rd party SaaS applications and internally developed applications that are connected to TrustBridge. There are other internally developed applications that are directly integrated to Okta. Okta provides identity and access management for users via single sign-on for employees.* 

*Please insert a high level architecture diagram of this system, describe the interaction between the components, and how the system interacts with the surrounding ecosystem (2-3 paragraph max). Decide if the go/rings classifications and expectations apply to this system.*  
*…*  
*![][image1]*  
*Current AD Agents in .biz \- ltx1-okta01, ltx1-okta08, eam1-okta01, esg3-okta01, wus2iamwuprd17, lva1-okta05, lva1-okta06*  
*Current AD Agents in China \- abe2-cokta01, abe2-cokta02 & abe2-cokta03*

Okta Active Directory (AD) Agents are lightweight Windows services that act as a secure connector between on-premises Active Directory environments and the Okta cloud.  They are designed with “zero inbound connectivity,” meaning Okta never opens a port into your network. Instead, the agents poll outbound to Okta over HTTPS on port 443\.  Core Functions include Directory sync of users, groups, and attributes from AD → Okta, Authentication validation of user access during login to Okta using AD via Delegated Authentication (DelAuth) securely without exposing AD externally, Group & Profile Lifecycle changes where changes in AD are imported into Okta via hourly imports,

Agents use a high-security design where only outbound connections via TLS are used to communicate. No VPN tunnels or firewall holes inbound are required.

Okta AD Agents are effectively stateless.  They do not maintain persistent shared state across agents and do not write identity–relevant or session–relevant data locally.

They function as lightweight connectors that: 

* Authenticate outbound to Okta over HTTPS (mutual TLS)   
* Poll Okta for tasks (user provisioning, deprovisioning, group updates, directory sync)   
* Relay password and group membership changes from AD to Okta   
* Execute delegated authentication (password verification) when configured   
* If an agent fails, another agent can take over immediately with no synchronization needed.

There is no agent-to-agent communication. This is by design for resiliency and simplicity. No quorum system exists. Instead, they operate using a hub-and-spoke pattern:

* Hub → Okta service  
* Spokes → AD agents  
* Okta assigns tasks to whichever healthy agent is available.

[Okta password less (regular user flow) and password flows (automation)](https://linkedin.atlassian.net/wiki/spaces/ENGS/pages/1086850355/Okta+Password+less+and+Password+flow+diagrams)

Okta Non-Production instance: [https://linkedin.oktapreview.com](https://linkedin.oktapreview.com) 

### Impact to Linkedin

*What is the impact to Linkedin when this system fails?*  
*If Okta goes down, users cannot login to applications via single sign-on. Access to critical applications such as VPN, TrustBridge, SalesForce, Slack, WorkDay will not be available.*

### Service Dependencies

*What services do you rely on to function and what happens if they are unavailable or slow? Are there any cross fabric dependencies (including replication)?*

| Dependency | Is it cross-fabric? | Dependency [Ring](http://go/rings/inventory) | Why | Impact  |
| :---- | :---- | :---- | :---- | :---- |
| Network Connectivity | Yes | 0 | Okta users authentication, data imports from AD depends on stable network links and NACLs. | Authentication fails – Delegated authentication of users to Okta for establishing new Okta sessions fails if connectivity to AD is not available. Access to AD resources stops – User AD records, groups become unreachable. AD Replication halts – Active Directory domain controllers cannot sync changes which prevents the latest AD user resources to propagate into Okta. Critical services break – DNS resolution, Group Policy updates, and SSO fail. Cloud integration disrupted – Okta AWS cloud.  Delayed logins – authentication requests take longer or time out. Replication latency increases – inconsistent directory data across sites. Higher error rates – intermittent failures in DNS lookups. |
| VMware Platform | No | 0 | Our AD agents run on Virtual Machines hosted on VMware platform | vCenter is required for us to be able to login to the VMs to troubleshoot issues. |
| Active Directory | No | 1 | Okta relies on Active Directory to ensure users can authenticate in to Okta, import latest AD user information and group information. | Authentication fails – Delegated authentication of users using password to Okta for establishing new Okta sessions fails if connectivity to AD is not available. Access to AD resources stops – User AD records, groups become unreachable. End user devices clock time need to be in sync, time drifts in the NTP service will result in device trust failures. |
| Azure  | No | 0 | Our AD agents run on Azure VMs | Azure components are required for us to login to the VMs to troubleshoot issues.  Connectivity loss: ExpressRoute failure severs on-prem to Azure.  |

### Okta service also has a dependency on non Ring services such as Network and VMware. 

### Software Library Dependencies

*Are there any critical dependencies (language runtime, or the component itself if it is open source) that are severely outdated? Did you pull in new libraries to the company through ELR and are they active? For newly ELR’ed dependencies, please list the dates of the last 2 major or minor releases.*  
*…*  
*Not Applicable \- The Okta AD agent is an Okta provided 3rd party software and does not rely on additional third-party libraries that need to be manually sourced or installed beyond the required system prerequisites of (Windows Server 2016, 2019, 2022, or 2025 and .NET Framework 4.6.2 or later). The installer is designed to run within the required Windows environment. The only way to do the install of the agent is via a user interface screen (UI) where credentials are entered to configure and run the agent.*

*The Okta AD agent is an Okta provided 3rd party software and does not rely on additional third-party libraries that need to be manually sourced or installed beyond the required system prerequisites of (Windows Server 2016, 2019, 2022, or 2025 and .NET Framework 4.6.2 or later). The installer is designed to run within the required Windows environment. The only way to do the install of the agent is via a user interface screen (UI) where credentials are entered to configure and run the agent.* 

### Data Lineage

*If you depend on input data that is produced via a data processing job (eg. Fedex feature or Flink job), do you have alerts/metrics/observability on the production pipeline(s) of all of your data dependencies? Are your dependencies visible in DataHub?*  
*…*  
*Not Applicable*

### Runtime Configs

*Are critical configuration parameters set for the application, such as minimum/maximum heap size? If the application is running custom non-default runtime parameters, are the reasons for these well documented and understood?*  
***…***  
*Not Applicable*

## **Observability**

### Metrics/Dashboards

*We expect most operational metrics to be nearly-live and have a freshness of 5min or less. If you have any operational metric that is not nearly-live, please call them out.*

**Link to Metrics Dashboard:**  
*Are you using MDM and Observe for your operational metrics? If not, why not?*

[https://observe.prod.linkedin.com/g/d/fdv6960l4i4z430768/okta-master-dashboard?orgId=1\&var-query0=All\&from=now-12h\&to=now](https://observe.prod.linkedin.com/g/d/fdv6960l4i4z430768/okta-master-dashboard?orgId=1&var-query0=All&from=now-12h&to=now)

**Standard System Metrics**  
*Please certify that you are monitoring the following metrics. Please ignore this if you are running on the standard LinkedIn restli/grpc stack because these metrics are provided by default on the standard stack.* 

- [x] CPU usage (unit: %)  
- [x] Disk Usage  
- [x] System Heartbeat  
- [x] System Up Time  
- [x] Memory Usage

**Domain-specific metrics**  
*What are the metrics that your users and/or experts of this domain would expect you to monitor?* 

[Okta prober monitor](https://portal.azure.com/#view/Microsoft_OperationsManagementSuite_Workspace/Logs.ReactView/source/Microsoft_Azure_Monitoring_Alerts.ViewAlertRuleDetails.ReactView/query/NWConnectionMonitorTestResult%0A%7C%20where%20ConnectionMonitorResourceId%20%3D%3D%20%27%2Fsubscriptions%2F56204fcb-3a27-4b69-ab1e-ba3dd94c9f33%2FresourceGroups%2Fnetworkwatcherrg%2Fproviders%2FMicrosoft.Network%2FnetworkWatchers%2FNetworkWatcher_westus2%2FconnectionMonitors%2Foktawus2checks%27%0A%7C%20where%20TestResult%20!%3D%20%22Pass%22%0A%7C%20project%20TimeGenerated%2C%20SourceName%2C%20DestinationName%2C%20DestinationAddress%2C%20TestResult/resourceId/%2Fsubscriptions%2F56204fcb-3a27-4b69-ab1e-ba3dd94c9f33%2FresourceGroups%2Fmonitoring%2Fproviders%2FMicrosoft.OperationalInsights%2Fworkspaces%2Fadcse-prd-logan-6bvkdxqeqzbuu)  
Okta AD agent status  
Okta AD agent connectivity to Okta Cloud

[https://ms.portal.azure.com/\#view/Microsoft\_Azure\_Monitoring\_Alerts/AlertRulesBlade/resourceId/%2Fsubscriptions%2F56204fcb-3a27-4b69-ab1e-ba3dd94c9f33%2FresourceGroups%2Fmonitoring%2Fproviders%2FMicrosoft.OperationalInsights%2Fworkspaces%2Fadcse-prd-logan-6bvkdxqeqzbuu](https://ms.portal.azure.com/#view/Microsoft_Azure_Monitoring_Alerts/AlertRulesBlade/resourceId/%2Fsubscriptions%2F56204fcb-3a27-4b69-ab1e-ba3dd94c9f33%2FresourceGroups%2Fmonitoring%2Fproviders%2FMicrosoft.OperationalInsights%2Fworkspaces%2Fadcse-prd-logan-6bvkdxqeqzbuu)

**Dependency-specific metrics** (think success rate, latency, quota usage, replication speed, etc.)

- [x] Network Availability  
- [x] vCenter Availability

### Events and Informed

*Are you planning to push any type of events into our change capture Events system, [inEvents](http://go/inevents)? If so, what kind of change events?*

*NO* 

### Distributed Traces

*Is this service part of the online stack? If so, does it integrate with the LinkedIn distributed trace? If not, why not? You can search for traces from your service by going to [go/trace-explorer](http://go/trace-explorer).*

*NO*

### SLOs

*What are the metrics that show the callers are having expected experience? Do you have objectives set up on those metrics? Do you have alerts set up that would warn you before your SLOs are compromised? Please link to your SLO page (preferably on Observe).*

*Since Okta is a 3rd party SaaS provider they are obligated to provide 99.99% service uptime.*   
[*https://status.okta.com/?\_gl=1\*9yvnfq\*\_gcl\_au\*ODU0NzE3NDg4LjE3NTg3MzA4ODA.\*\_ga\*ODg2OTg5OTM1LjE3NjIyMTQ0Nzg.\*\_ga\_QKMSDV5369\*czE3NjM0MzU1MzckbzE3JGcwJHQxNzYzNDM1NTM3JGo2MCRsMCRoMA..*](https://status.okta.com/?_gl=1*9yvnfq*_gcl_au*ODU0NzE3NDg4LjE3NTg3MzA4ODA.*_ga*ODg2OTg5OTM1LjE3NjIyMTQ0Nzg.*_ga_QKMSDV5369*czE3NjM0MzU1MzckbzE3JGcwJHQxNzYzNDM1NTM3JGo2MCRsMCRoMA..)

### Alerts

*Please link to where the alerts are defined. If the alerts are not defined in Observe, please explain why not.*  
*…*

- [x] *Does each alert listed above have a linked runbook in the alert?*  
      *NO*  
        
- [x] *Do the alerts fire even if all instances go down and stop sending any metrics (therefore, there are no time series reported to MDM)? This is to make sure you’re handling NaNs correctly or using [replacenulls](https://eng.ms/docs/products/geneva/metrics/advanced/kql/datatypes/nullvalues) in your KQL-M queries. Please test it.*  
      As our metrics are not in MDM, we are monitoring the last heartbeat time stamp from Azure Monitor. 

- [x] Does your system have critical indicators of service health onboarded to the Site Health Zone? These are used to make high sev incident and fabric fail out decisions.  
      Not Applicable.

### Logs

Make sure your application logs are present in InLogs/Observe. Please include a link to your logs in Observe [Logs Explorer](https://observe.prod.linkedin.com/logs-explorer). If they are not present, please follow the onboarding instructions at [go/inlogs/onboard](https://go/inlogs/onboard).

* Okta Logs are in Azure Log Analytics WorkSpace

* System Metrics: [https://portal.azure.com/\#@lnkdprod.onmicrosoft.com/resource/subscriptions/56204fcb-3a27-4b69-ab1e-ba3dd94c9f33/resourceGroups/monitoring/providers/Microsoft.OperationalInsights/workspaces/adcse-prd-logan-6bvkdxqeqzbuu/Overview](https://portal.azure.com/#@lnkdprod.onmicrosoft.com/resource/subscriptions/56204fcb-3a27-4b69-ab1e-ba3dd94c9f33/resourceGroups/monitoring/providers/Microsoft.OperationalInsights/workspaces/adcse-prd-logan-6bvkdxqeqzbuu/Overview)  
* Security Events:  
  [https://portal.azure.com/\#@lnkdprod.onmicrosoft.com/resource/subscriptions/0e3f21be-644d-44a2-8fee-cefb5db2e48d/resourceGroups/azure-insight/providers/Microsoft.OperationalInsights/workspaces/wus2-insight-workspace/Overview](https://portal.azure.com/#@lnkdprod.onmicrosoft.com/resource/subscriptions/0e3f21be-644d-44a2-8fee-cefb5db2e48d/resourceGroups/azure-insight/providers/Microsoft.OperationalInsights/workspaces/wus2-insight-workspace/Overview)

## **Failure Modes**

*Document all potential failure modes and their impacts. Explain how aspects like (1) downtime, (2) latency, and (3) correctness/relevance bugs can impact the functionality provided. Ensure that all hard and soft failure modes are documented and well understood. Please also denote how wide the blast radius is when the failure occurs (single user, single node, entire fabric, all of linkedin.com, etc.)*

### 

### Service Failure

*Does this system introduce new failure modes to LinkedIn.com that did not exist previously? Please list out all new failure modes in the table below.*

*NO* 

*For systems with multiple components, what happens when an individual component in the system fails? Please list out all new failure modes in the table below.*  
*…*

| Component | New Failure Modes When It Fails |
| :---- | :---- |
| Active Directory | \- Okta User authentication fails \- Directory lookups break (latest user records, user attributes, groups data are not available for import into Okta)   [Ref: Active Directory (.biz) PRR document](https://docs.google.com/document/d/1R8YTfFOr6ecufcjX_aAHu1tYezRX4-Xtr9ByzeiW0tM/edit?tab=t.0#headin…) |

### Dependency Failure

*Does this system or the components of this system tolerate failure of a single node/single instance?*  
…  
Yes \- Okta Active Directory agents are designed to work in an Active / Active mode where if one AD agent fails, the other AD agents continue to function. These AD agents are deployed across multiple data centers.

*Does the system tolerate an entire fabric restarting (power off and power on)? Can the system handle every instance inside a single fabric all stopping and restarting (concurrently)?*  
…  
For .biz domain \- Yes \- Okta Active Directory agents are designed to work in an Active / Active mode where if one AD agent fails, the other AD agents continue to function. These AD agents are deployed across multiple data centers.

For .cn domain \- No \- We have AD agents in ABE2. We will need to deploy AD agents in the ESG3 data center.

*How does the system handle its declared service dependencies failing? Does the system need to quickly detect failures caused by dependency failure? Is there a way for the system to mitigate against a dependency failing.*  
…  
Okta Active Directory agents are designed to work in an Active / Active mode where if one AD agent fails, the other AD agents continue to function.

### Protection From Users

*Do you provide a standard client for users of your system? Does the client handle common failure modes, like increased latency, errors, and timeouts, gracefully?*   
…  
Not applicable \- Okta actively prevents and mitigates DDoS attacks through multi-layered defenses, including AWS WAF for filtering, rate limiting on APIs, blocking malicious IPs globally via ThreatInsight, using advanced controls at the edge and Integrates with bot management tools and CAPTCHAs to distinguish human users from automated bots.  
Brute Force attacks, Password Sprays are prevented through ThreatInsight  
Anonymizer access is blocked via Network block rules  
By default, Okta API tokens and OAuth 2.0 apps are configured to use 50% of an API endpoint's rate limit when they're created through the Admin Console.  
https://developer.okta.com/docs/reference/rate-limits/

*Does your system protect most of your callers from a single mis-behaving caller? What is the expected load that a single caller should be able to make?*  
…  
Not applicable

*For RPC services, do nodes of your system implement overload protection? Does your system use the LinkedIn standard single node overload protection, Hodor? If not, why not.*  
*…*  
Not Applicable

*Does your system have a quota management system in place for its callers? Does your system use the LinkedIn standard quota management system, **Liminal**, to manage quotas? If not, why not.*  
*…*  
Not Applicable

### Protecting Your Users

*Does this system process control plane inputs from upstream teams? For example, taking on a new workload definition, lix iteration, d2 configuration, etc. If so, can users test out the new iteration of the input without affecting production? What mechanism do you have in place to prevent users from submitting a bad configuration/definition/workload?*  
*…*  
*Users need to use PRMFA to access Okta assets. Any user who can make changes to Okta need to have elevated privileges which are governed by change management and audit processes.*

*For any specific user initiated changes that need to be pushed to Okta production, the changes are first implemented and tested in Okta non-production instance.*

*Can users ramp out the new iteration of the configuration onto one or a small subset of the compute nodes/jobs before applying it to an entire fabric? Can users ramp the changes to one fabric at a time?*  
*…*  
*Okta application assignments are done via AD groups, service owners can determine first to deploy the app to a subset of users for testing and later to deploy the app to the target set of users by adding those users to the AD group(s).*

### Misc

*Please include anything else here that was not covered previously.*  
…  
NONE

| Failure Mode | Impact | Blast Radius and Max Severity | Detection Plan | Mitigation Plan |
| :---- | :---- | :---- | :---- | :---- |
|  |  |  |  |  |

## **Scalability**

### Known Hard Limitations

*What are the scale boundaries that you know you can push to? Are there any theoretical or known hard limitations? Can they be mitigated?*

*NONE \- Yes, we do take the following scaling consideration when implementing Okta AD*  
   
*Ensure that we have 3+ Okta AD agents for 30k users – we have 7 agents and*  
*Ensure servers running agents meet minimum specs (2 CPU, 8GB RAM) and have fast network links to domain controllers.*  
   
*Overall Okta platform scales dynamically, supporting vast user bases.*   
 

| Dimension |  | Description |
| :---- | ----- | :---- |
|  |  |  |

### Known Eventual Scaling Constraints

*What are the dimensions that impact this component’s scalability aspects and throughput/latency/SLOs?*

*NONE*

| Dimension | Impact to Throughput/Latency |
| :---- | :---- |
|  |  |

## **Operational Response**

- [x] *Is the on-call rotation setup and tested?*   
      *The on-call rotation is setup on [https://go/oncall](https://go/oncall) \- the team name is “infosec-sso”*  
      [*https://oncall.prod.linkedin.com/team/team/infosec-sso*](https://oncall.prod.linkedin.com/team/team/infosec-sso)  
        
- [x] *Do the on-calls know how to escalate and is the procedure standard when progress is stuck during an incident? Please include a link to the escalation process.*

	*Link will be provided.*

- [ ] *Do the on-calls know how to find the health of all of the downstream dependencies and the escalation path for each of them?*

	*Yes*

- [ ] *Is every member of your on-call rotation knowledgeable enough (or taken enough training) to be for on-call?*

	*Yes*

- [ ] *Are your assets mapped with crew id? (Multiproducts, PEM Product Flows, Callisto Pages, etc.) Your partner teams should be able to identify you as the owner of your system easily.*

Yes \- Okta product is owned by Corporate Identity Crew.

- [ ] *Do you have a website (github pages, wiki, or readme markdown) containing the following information:*  
      - [x] ~~Design and Architecture: …~~  
            [Page: Okta Design and Architecture Overview | OktaDesignandArchitectureOverview SystemArchitectureDiagram](https://linkedin.atlassian.net/wiki/spaces/ENGS/pages/525301790/Okta+Design+and+Architecture+Overview#OktaDesignandArchitectureOverview-SystemArchitectureDiagram)  
      - [x] ~~Runbooks: …~~  
            [Page: Identity and Access Management (IAM) Runbook](https://linkedin.atlassian.net/wiki/spaces/ENGS/pages/525266432/Identity+and+Access+Management+IAM+Runbook)  
      - [x] ~~Metrics Dashboards: …~~

      [https://observe.prod.linkedin.com/g/d/fdv6960l4i4z430768/okta-master-dashboard?orgId=1\&var-query0=All\&from=now-12h\&to=now](https://observe.prod.linkedin.com/g/d/fdv6960l4i4z430768/okta-master-dashboard?orgId=1&var-query0=All&from=now-12h&to=now)

      - [ ] Viewing Logs: …  
      - [ ] Audit Logs: …   
      - [x] ~~GitHub repository: …~~  
            Not Applicable  
      - [x] ~~Your go/oncall team: …~~

      *The on-call rotation is setup on [https://go/oncall](https://go/oncall) \- the team name is “infosec-sso”*

      - [x] ~~Alert slack channel (if one exists): …~~  
            No separate Alert Slack Channel. We have an “ask\_iam” channel where issues are addressed.  
- [ ] *Are there human-driven operations that are not listed in the runbooks?*  
      - [ ] …  
            Not Applicable

## **Capacity** 

### Capacity Management

*Does your system have enough capacity to serve the initial demand? How was this determined? If we did not use ForgeFire or Dyno to figure out the capacity needs, please briefly mention why not?*  
…  
Yes—capacity planning for Okta AD agents VM typically ensures that the system can handle expected load during peak usage while maintaining performance and reliability. The goal is to keep utilization within safe thresholds (e.g., CPU at \~40% during peak periods) so there’s room for growth and failover without impacting user experience. 

*Does your system have a capacity management strategy in place? Does it account for a single fabric failing out and a deployment occurring in one of the remaining two active fabrics? (Do you have a process for ensuring there’s enough capacity to prevent performance degradation or outages?)*  
…  
Yes. Capacity management for Okta AD agents is proactive, not reactive. It involves designing, sizing, and monitoring the environment so utilization trends stay within defined thresholds and scaling actions occur before user impact. The strategy includes:

* Baseline targets: Keep CPU utilization around 40% during peak periods to allow headroom for failover and growth.  
* Alert thresholds: Trigger alerts at 90% utilization for 5 minutes to initiate scaling or failover actions.  
* Redundancy planning: Deploy multiple Okta AD agents across datacenters to avoid single points of failure. 

Okta AD agents architecture and capacity planning explicitly consider failure domain isolation and multi-zone resiliency:

* Multiple Okta AD agents per datacenter  
* Cross-fabric failover  
* Geographically dispersed deployments  
* Failover testing


Capacity planning involves:

* Size hardware and domain controllers for peak load \+ failover scenarios.  
  * Track CPU, memory, disk I/O, and replication latency.  
  * Use automated alerts for threshold breaches.   
  * Conduct failover drills 

*What metrics do you examine to understand if your capacity has reached saturation? Common saturation metrics are request concurrency, cpu/memory utilization, GC score, QPS/node.*  
…  
[https://observe.prod.linkedin.com/g/d/fdv6960l4i4z430768/okta-master-dashboard?orgId=1\&var-query0=All\&from=now-12h\&to=now](https://observe.prod.linkedin.com/g/d/fdv6960l4i4z430768/okta-master-dashboard?orgId=1&var-query0=All&from=now-12h&to=now)

*Do your downstream dependencies have enough capacity to serve the new load generated by your system, especially during a fabric fallout? How did you validate this, and how are you monitoring the downstream “quota” health as your system grows in usage.*  
…  
Not Applicable

*For systems that have slightly delayed data processing (Samza, cross colo replication, etc.), how much processing throughput does the system have compared to steady state? In cases where the processing falls behind, how quickly can it catch up to the latest? The expectation is that for catch up reasons, we have AT LEAST 2x processing capacity as normal steady state.*   
…  
Not Applicable

*Is there auto-scaling enabled? If not, explain why?*  
…  
Not Applicable

*Have you performed any load or performance testing of your system? Did you use [ForgeFire](https://linkedin.atlassian.net/wiki/spaces/SOP/pages/495426701/ForgeFire+SLTaaS+CLI+User+Guide#) (LinkedIn’s distributed load test tool).?*  
*…*  
*No \- the Okta AD agents’ performance is monitored through our alerts.*

*For projects that significantly modify existing service(s) or workload(s), have you notified the capacity forecast and management team about your project and ramp timeline?*  
*…*  
Not Applicable

### Resource allocation

* *How much memory/CPU does each instance of this system consume during peak traffic and why:  …We have metrics that track the memory/cpu usage.*  
* *Was this system accounted for in the current year’s forecast?  If not, explain why?*

	Not Applicable

## **Deployments**

*How frequently do you deploy?*  
…  
Okta changes aren’t deployed like a typical application or service. Instead, changes fall into three categories:

Okta AD agent upgrades:  
These are typically yearly updates. Updates are rolled out in a staged manner: non-prod → few prod Okta AD agents \-\> remaining agents.

Okta cloud changes (Release Notes):  
These are driven by Okta.   
[Okta Identity Engine release notes (Production)](https://help.okta.com/oie/en-us/content/topics/releasenotes/production.htm).

Enabling new features in Okta:  
These are rare and always validated in a staging domain before being pushed into Production.

*How do you validate changes to your software? Do you have any code coverage enforcement?*   
*…*  
We validate changes:

* Peer review for all operational changes following the Change Management process.  
* Staging environment validation for changes

This ensures functional correctness even without code-level tests.

*Do you use EKG? If so, are the rules accurate and comprehensive?*  
*…*  
*Not Applicable*

*What is the first set of users that experience any new release of your system? Is it users within your team or engineers at LinkedIn? If not, why not?*  
*…*  
*The first set of users that experience any new feature or functionality changes is within the IAM team.*

*Do you use the standard deployment system (CRT or LCD)? If not, why not?*  
*…*  
We do not use CRT or LCD because Okta AD agents run on Windows VMs and are not deployed through LinkedIn’s deployment stack. 

*What system do you use to store and deploy static and dynamic configurations (puppet, config2, dyco, lix, something else, or all of above)?*  
*…*  
*Not Applicable \- The configuration is entered into the UI when installing the Okta AD agent and can only be done this way.*  
   
[*https://support.okta.com/help/s/question/0D54z00007FhDulCAF/automate-installation-of-the-active-directory-ad-agent?language=en\_US*](https://support.okta.com/help/s/question/0D54z00007FhDulCAF/automate-installation-of-the-active-directory-ad-agent?language=en_US)

*Is your system deployed to all available fabrics? Can your system tolerate any one fabric being offline for an unlimited duration?*  
…  
Okta AD agents are deployed across several LinkedIn Data centers. Losing a datacenter does not impact global authentication, as other datacenters continue to serve traffic.

*Do you deploy serially or in parallel to multiple fabrics concurrently? If multi-fabric parallel deployment is required, why?*  
…  
*Not Applicable \- We deploy serially one Okta AD agent per data center per Geo. Multi datacenter parallel deployment is not required.*

*How much bake time do you have between steps?*  
…  
*Not Applicable \- We allow 1 week bake time.*

*Have you configured a standard Mon-Fri deployment window?*  
…  
*Not Applicable \- No, we have not defined a M-F deployment window as our deployments are designed to be seamless and cause no disruption to the Okta service.*

*Does your runbook or operational documentation have a link to [the emergency deployment procedure](http://go/emergencydeploy) when EngX, LCD, or CRT are down?*   
*…*  
*Not Applicable*

### Auto-rollouts

*Does the deployment of new code changes require human intervention (is it touchless)?*  
…  
*Not Applicable \- Our deployments are done by engineers. There is no current way to automate this. https://support.okta.com/help/s/question/0D54z00007FhDulCAF/automate-installation-of-the-active-directory-ad-agent?language=en\_US*

*What stops a buggy deployment after a deployment starts?*  
…  
*Not Applicable*

### Rollbacks

*What is your rollback strategy when a new deployment causes issues?*  
…  
*Okta AD agent upgrades: Roll back to previous version and restart the agent.*  
*Okta feature enablement: Roll back feature and communicate to target users.*

*Have you exercised any rollbacks? How do you know your rollback strategy works and continue to work?*  
…  
 Rollback procedures are tested:

* In staging domain  
* Through DR exercises  
* Via incident postmortems

*How do you prevent any changes that are not ok to roll back from getting rolled back? If any non-rollbackable changes need to go out, how are you tracking those?*  
…  
Non-rollbackable items (Okta tenant upgrade) are:

* Tracked via project plans with detailed project tasks & adequate testing   
* Logged in change management systems & peer reviewed.  
* Executed only after staging validation.

## **Migration**

*If this system does not require a migration, please ignore this section.*

*Not Applicable*

*Please describe or link to a doc that describes the migration design and major milestones.*  
*…*

*Please describe the rollback strategy if something goes wrong during migration.*  
*…*

*Please list metrics that tell us if the migration is going well operationally. We want to see at least 1 success rate (availability or equivalent) metric and 1 latency metric. Ideally there is a success rate and latency of both the old system and the new system.*

- [ ] Success rate \#1:  
      - [ ] Latency \#1:

*Please list metrics that can show migration is consuming the expected amount of compute and memory. If there is an increase that is expected, has the increase been communicated to with the partner teams.*

- [ ] Compute/Latency:  
      - [ ] Memory Utilization:

*Please list one or more showing the migration progress.*  
*…*

## **Disaster Recovery**

*(If the component stores state) explain how you are backing data up and whether you have exercised restores:*  
…  
Okta is a cloud service that provides disaster recovery functionality as part of our contractual obligation. The time to bring the service up during DR is 60 mins.

Okta does provide a recent offering of an “Enhanced Disaster Recovery” solution that requires additional commercials and further investigation.

*(If the component stores state) Link to the restore procedure:*  
…  
Not applicable

*How does the component perform in a full datacenter reboot scenario? Can upstreams/downstreams fail gracefully?*  
…  
Not applicable

*Does the component self-recover from cold start scenarios?*  
…  
Not applicable

*Does the component self-recover when something blocking its launch/functionality recovers?*  
…  
Not applicable

## **Security**

*Does the system need to go through a TDR? See [go/tdr](http://go/tdr) for a list of criteria that would make TDR required.*

*No. Okta product and features have been vetted through Information security third party security assessment.*

## **Known issues**

*Are there any overdue action items from past incidents for your system?*

* …  
* …
