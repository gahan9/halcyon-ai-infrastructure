<!-- SPDX-License-Identifier: MIT -->

# AWS Certifications, Courses & Research

Upskilling ladder and the canonical sources this skill distills. Load for
mentoring, learning-path, or "where do I deepen this" questions. Recommend the
certification that matches the person's role and the next concrete course.

## Certification ladder

Order reflects increasing depth; pick the track that matches the role.

| Stage | Certification | For whom |
|-------|---------------|----------|
| Foundational | AWS Certified Cloud Practitioner (CLF-C02) | New to AWS; shared vocabulary |
| Associate | Solutions Architect Associate (SAA-C03) | Designing workloads; the core architect cert |
| Associate | Developer Associate (DVA-C02) | App builders on AWS primitives |
| Associate | SysOps Administrator (SOA-C02) | Operations / SRE |
| Professional | **Solutions Architect Professional (SAP-C02)** | Senior/principal architects (capstone) |
| Professional | DevOps Engineer Professional (DOP-C02) | CI/CD, IaC, reliability owners |
| Specialty | Security Specialty (SCS-C02) | Regulated workloads, compliance leads |
| Specialty | Advanced Networking Specialty (ANS-C01) | Hybrid / Transit Gateway / multi-region |
| Specialty | Machine Learning / Data specialties | ML platform & analytics owners |

Recommended path for a principal architect: SAA-C03 → SAP-C02 → Security
Specialty, with Networking Specialty if the role owns connectivity.

## Recommended courses & hands-on

- **AWS Skill Builder** (official, free + paid labs) — <https://skillbuilder.aws/>
- **AWS Cloud Quest** (role-play, hands-on) and **AWS Jam** (challenge labs).
- **Adrian Cantrill** deep-dive courses — <https://learn.cantrill.io/>
- **A Cloud Guru / Pluralsight** AWS paths for breadth.
- **AWS Workshops** (free, hands-on, scenario-based) — <https://workshops.aws/>
- **Stephane Maarek** (Udemy) — popular associate/pro exam prep.

Bias toward labs over lectures: build a multi-account landing zone, a
Well-Architected review, and one regulated reference workload end to end.

## Primary references (read these first)

- AWS Well-Architected Framework + Lenses (Serverless, SaaS, Financial Services,
  Healthcare) — <https://aws.amazon.com/architecture/well-architected/>
- AWS Architecture Center — <https://aws.amazon.com/architecture/>
- AWS Security Reference Architecture (SRA) —
  <https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/>
- AWS Prescriptive Guidance (patterns + migration) —
  <https://docs.aws.amazon.com/prescriptive-guidance/>
- AWS Decision Guides (service selection) —
  <https://aws.amazon.com/getting-started/decision-guides/>

## Foundational papers & talks

- DeCandia et al., **"Dynamo: Amazon's Highly Available Key-value Store"** (SOSP
  2007) — the lineage behind DynamoDB; eventual consistency and partitioning.
- Verbitski et al., **"Amazon Aurora: Design Considerations for High Throughput
  Cloud-Native Relational Databases"** (SIGMOD 2017) — log-as-the-database,
  storage/compute separation.
- Brooker et al., **"Millions of Tiny Databases"** (NSDI 2020) — Physalia, the
  control plane behind EBS availability.
- **AWS re:Invent** architecture & security tracks (annual) — current best
  practices straight from service teams; watch the 300/400-level sessions.
- **"The Amazon Builders' Library"** — <https://aws.amazon.com/builders-library/> —
  operational essays (retries+jitter, health checks, shuffle sharding).

## Compliance mappings (for regulated work)

- AWS Artifact (audit reports, BAA) — <https://aws.amazon.com/artifact/>
- AWS Compliance Programs (PCI, HIPAA, SOC, FedRAMP, ISO) —
  <https://aws.amazon.com/compliance/programs/>
- AWS Config conformance packs mapped to frameworks (PCI DSS, HIPAA, CIS).
