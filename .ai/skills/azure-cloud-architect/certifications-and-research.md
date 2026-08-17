<!-- SPDX-License-Identifier: MIT -->

# Azure Certifications, Courses & Research

Upskilling ladder and the canonical sources this skill distills. Load for
mentoring, learning-path, or "where do I deepen this" questions. Recommend the
certification that matches the person's role and the next concrete course.

## Certification ladder

| Stage | Certification | For whom |
|-------|---------------|----------|
| Foundational | Azure Fundamentals (AZ-900) | New to Azure; shared vocabulary |
| Associate | Azure Administrator (AZ-104) | Operations / platform |
| Associate | Azure Developer (AZ-204) | App builders on Azure primitives |
| Expert | **Azure Solutions Architect Expert (AZ-305)** | Senior/principal architects (the core cert) |
| Expert | DevOps Engineer Expert (AZ-400) | CI/CD, IaC, reliability owners |
| Specialty | Azure Security Engineer (AZ-500) | Regulated workloads, compliance leads |
| Specialty | Azure Network Engineer (AZ-700) | Hub-spoke / Virtual WAN / Private Link owners |
| Specialty | Azure Cosmos DB Developer (DP-420) / Data Engineer (DP-203) | Data platform owners |

Recommended path for a principal architect: AZ-104 → AZ-305 → AZ-500, adding
AZ-700 if the role owns connectivity. (AZ-305 requires AZ-104 fundamentals.)

## Recommended courses & hands-on

- **Microsoft Learn** (official, free paths + sandboxes) — <https://learn.microsoft.com/training/>
- **Microsoft Applied Skills** (scenario-based credentials).
- **Azure Architecture Center** reference architectures + example workloads.
- **Pluralsight / A Cloud Guru** Azure paths for breadth and exam prep.
- **John Savill's Technical Training** (YouTube) — deep, free Azure study guides.

Bias toward labs over lectures: deploy an ALZ accelerator, run a Well-Architected
review, and build one regulated reference workload end to end.

## Primary references (read these first)

- Azure Well-Architected Framework — <https://learn.microsoft.com/azure/well-architected/>
- Cloud Adoption Framework (CAF) — <https://learn.microsoft.com/azure/cloud-adoption-framework/>
- Azure Architecture Center (patterns + reference architectures) —
  <https://learn.microsoft.com/azure/architecture/>
- Cloud Design Patterns (catalog) —
  <https://learn.microsoft.com/azure/architecture/patterns/>
- Azure Landing Zones —
  <https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/>

## Foundational papers & talks

- DeWitt/microsoft research lineage aside, study the **Cloud Design Patterns**
  catalog (Ambassador, Bulkhead, Circuit Breaker, CQRS, Saga, Strangler Fig,
  Sidecar) — Azure documents these as first-class architectural building blocks.
- Microsoft Research, **"Azure Accelerated Networking: SmartNICs in the Public
  Cloud"** (NSDI 2018) — FPGA-based host networking behind Azure VMs.
- Microsoft, **"Service Fabric: A Distributed Platform for Building
  Microservices in the Cloud"** (EuroSys 2018) — the platform behind many Azure
  services.
- **Microsoft Ignite / Build** architecture & security sessions (annual) —
  current best practices from product teams.
- **Designing Distributed Systems** (Brendan Burns) — patterns that map directly
  onto Container Apps / AKS designs.

## Compliance mappings (for regulated work)

- Microsoft Purview Compliance Manager (assessments, evidence) —
  <https://learn.microsoft.com/purview/compliance-manager>
- Service Trust Portal (audit reports, SOC/ISO/PCI) —
  <https://servicetrust.microsoft.com/>
- Defender for Cloud regulatory compliance dashboard (PCI, HIPAA/HITRUST, ISO,
  CIS) mapped to live posture.
