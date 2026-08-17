<!-- SPDX-License-Identifier: MIT -->

# GCP Certifications, Courses & Research

Upskilling ladder and the canonical sources this skill distills. Load for
mentoring, learning-path, or "where do I deepen this" questions. Recommend the
certification that matches the person's role and the next concrete course.

## Certification ladder

| Stage | Certification | For whom |
|-------|---------------|----------|
| Foundational | Cloud Digital Leader | New to GCP; shared vocabulary, business framing |
| Associate | Associate Cloud Engineer | Deploy/operate basics |
| Professional | **Professional Cloud Architect** | Senior/principal architects (the core cert) |
| Professional | Professional Cloud Security Engineer | Regulated workloads, compliance leads |
| Professional | Professional Cloud Network Engineer | Shared VPC / hybrid / VPC SC owners |
| Professional | Professional Cloud DevOps Engineer | SRE, CI/CD, reliability owners |
| Professional | Professional Data Engineer | BigQuery/Dataflow analytics platform owners |
| Professional | Professional Cloud Database Engineer | Cloud SQL/Spanner/Bigtable owners |

Recommended path for a principal architect: Associate Cloud Engineer →
Professional Cloud Architect → Professional Cloud Security Engineer, adding
Network Engineer if the role owns connectivity.

## Recommended courses & hands-on

- **Google Cloud Skills Boost** (official, paths + labs) — <https://www.cloudskillsboost.google/>
- **Qwiklabs hands-on labs** and **skill badges** (scenario-based, graded).
- **Google Cloud Architecture Center tutorials** (reference, hands-on).
- **Coursera** — "Google Cloud Professional Cloud Architect" specialization
  (official) — <https://www.coursera.org/professional-certificates/gcp-cloud-architect>
- **A Cloud Guru / Pluralsight** GCP paths for breadth and exam prep.

Bias toward labs over lectures: build a CFT/Fabric FAST landing zone, an
Architecture Framework review, and one regulated reference workload end to end.

## Primary references (read these first)

- Google Cloud Architecture Framework — <https://cloud.google.com/architecture/framework>
- Google Cloud Architecture Center — <https://cloud.google.com/architecture>
- Enterprise foundations blueprint (security) —
  <https://cloud.google.com/architecture/security-foundations>
- Cloud Foundation Toolkit / Fabric FAST blueprints —
  <https://cloud.google.com/docs/terraform/blueprints/terraform-blueprints>
- Google SRE books (free) — <https://sre.google/books/>

## Foundational papers & talks

- Chang et al., **"Bigtable: A Distributed Storage System for Structured Data"**
  (OSDI 2006) — the model behind Cloud Bigtable.
- Corbett et al., **"Spanner: Google's Globally-Distributed Database"** (OSDI
  2012) — TrueTime, external consistency; the basis of Cloud Spanner.
- Melnik et al., **"Dremel: Interactive Analysis of Web-Scale Datasets"** (VLDB
  2010) — the engine lineage behind BigQuery.
- Akidau et al., **"The Dataflow Model"** (VLDB 2015) — unified batch/stream
  windowing behind Cloud Dataflow / Apache Beam.
- Burns et al., **"Borg, Omega, and Kubernetes"** (ACM Queue 2016) — the
  scheduling lineage behind GKE.
- **Google Cloud Next** architecture & security sessions (annual) — current best
  practices from service teams.

## Compliance mappings (for regulated work)

- Google Cloud compliance offerings (PCI, HIPAA, SOC, FedRAMP, ISO) —
  <https://cloud.google.com/security/compliance>
- Compliance Reports Manager (audit reports, BAA access).
- Assured Workloads for regulated/sovereign region and control enforcement.
