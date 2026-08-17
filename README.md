<!-- SPDX-License-Identifier: MIT -->

# Halcyon AI Infrastructure

Production platform design for Halcyon Labs (fictional), plus a later self-hosted 
inference design.

Built from the [project_template](../project_template) AI-config spine (all
skills under `.ai/skills/`), with Halcyon-specific architecture and client
intake documents.

## Recommendation in one sentence

For the six-week enterprise migration, run the API and workers on
**DigitalOcean App Platform**, store PDFs in **Spaces**, keep job records in
**managed PostgreSQL**, and use **managed Valkey** only as a work queue — not as
the sole place a job “exists.” Defer Kubernetes until the team has a platform
owner or a measured need.

Primary requirements map as: secure vendor-scoped upload → Spaces + auth;
async file queue → Valkey + Postgres ledger; inference → DO Serverless
Inference gateway; timeout/fail simulation → seeded non-production faults.

Details: [docs/recommendation/dana-recommendation.md](docs/recommendation/dana-recommendation.md)
and [docs/decisions/ADR-001-part1-platform.md](docs/decisions/ADR-001-part1-platform.md).

## Submission deliverables

| Deliverable | Link |
|-------------|------|
| Recommendation (primary) | [docs/recommendation/dana-recommendation.md](docs/recommendation/dana-recommendation.md) |
| Live staging endpoint | [healthz](https://halcyon-sim-staging-opauz.ondigitalocean.app/healthz) |
| Demo access (curl + limits) | [docs/evidence/access.md](docs/evidence/access.md) |
| Staging bring-up notes | [docs/evidence/staging-bring-up.md](docs/evidence/staging-bring-up.md) |
| Evidence gates (prod = FAIL) | [docs/evidence/README.md](docs/evidence/README.md) |

Staging uses temporary FakeAuth (any Bearer token). It is an exercise system,
not a production-ready claim.

## Current phase status

| Item | Status |
|------|--------|
| Repo + all skills | Done |
| Client clarification checklist | Done |
| Assumption log | Done — reversible defaults |
| Part 1 / Part 2 architecture docs | Done (proposed design) |
| Primary-requirement adaptation | Done — secure upload, vendor isolation, async queue, inference faults |
| Simulated app + Terraform + staging smoke | **Done** — live endpoint above |
| Production evidence gates | **FAIL** — load, soak, rollback, restore, security, headroom |


## Document map

| Audience | Document |
|----------|----------|
| Dana (client) | [docs/recommendation/dana-recommendation.md](docs/recommendation/dana-recommendation.md) |
| Dana (try the system) | [docs/evidence/access.md](docs/evidence/access.md) |
| Dana + FDE | [docs/client/assumption-log.md](docs/client/assumption-log.md) |
| Dana + CTO | [docs/architecture/tradeoffs-rpo-rto.md](docs/architecture/tradeoffs-rpo-rto.md) |
| Dana + CTO | [docs/architecture/tradeoffs-compute-platform.md](docs/architecture/tradeoffs-compute-platform.md) |
| Engineering | [docs/architecture/part1-production-platform.md](docs/architecture/part1-production-platform.md) |
| Engineering (alternative) | [docs/architecture/doks-exercise-variant.md](docs/architecture/doks-exercise-variant.md) |
| Engineering | [docs/architecture/part2-self-hosted-inference.md](docs/architecture/part2-self-hosted-inference.md) |
| Decision record | [docs/decisions/ADR-001-part1-platform.md](docs/decisions/ADR-001-part1-platform.md) |
| Future proof | [docs/evidence/README.md](docs/evidence/README.md) |
| Executive status | [pm/reports/exec-briefing-2026-08-15.md](pm/reports/exec-briefing-2026-08-15.md) |
| Executive slide | [presentations/2026-08-15-exec-briefing.pptx](presentations/2026-08-15-exec-briefing.pptx) |

## Repository layout

```
.ai/                         # Rules, hooks, skills (33), subagents, memory
docs/
  client/                    # Clarification checklist + assumption log
  architecture/              # Trade-offs, Part 1, Part 2
  decisions/                 # ADRs
  recommendation/            # Dana-facing recommendation
  evidence/                  # Access instructions, staging notes, prod gates
infra/terraform/             # Foundation modules + staging/production roots
app/                         # FastAPI simulation + worker
scripts/                     # Bootstrap, demo smoke, chaos helpers
pm/reports/                  # Dated executive briefings
presentations/               # Generated executive briefing slides
.env.example                 # Documented env vars (no secrets)
```

## Agent bootstrap

```bash
python .ai/setup-adapters.py
python .ai/setup-links.py
```

Canonical skills live under `.ai/skills/`. Prefer
`devops-automator` and `cluster-ops` (including DigitalOcean playbooks).

## Environment variables

Copy `.env.example` to `.env` locally. Never commit `.env`. See the table in
`.env.example` and [docs/architecture/part1-production-platform.md](docs/architecture/part1-production-platform.md).

## What comes next

1. Lock RPO/RTO envelope and Part 1 budget ceiling (Dana + CTO).
2. Close production evidence gates: load, soak, chaos, restore, security.
3. Choose identity provider; remove staging FakeAuth exception.
4. Human-gated production apply only after gates pass.

## License

MIT — see [LICENSE](LICENSE).
