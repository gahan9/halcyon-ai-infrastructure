<!-- SPDX-License-Identifier: MIT -->

# Client clarification checklist (for Dana)

**Purpose:** Answer these before we claim the platform is ready for the
enterprise migration. Each question includes **why we need this** and **what
decision it changes**. Plain language first; technical terms in parentheses
only when useful with vendors or enterprise customers.

**Status:** Awaiting Halcyon answers. Scaffold uses reversible assumptions in
[assumption-log.md](assumption-log.md) until then.

## Executive decision brief

- 🟡 **Health:** The design is ready for customer review, but production
  readiness is **blocked** by unanswered traffic, recovery, incident, budget,
  and data-handling questions.
- ✅ **Top recommendation:** Use App Platform with managed PostgreSQL, managed
  Valkey, and Spaces; automate delivery with Terraform and CI.
- ⚠️ **Decision needed:** Dana and the CTO should assign owners and answer the
  blocking questions below before implementation or DigitalOcean spend.

| Decision or input | Response owner | Needed by | Status / blocker |
|-------------------|----------------|-----------|------------------|
| Migration arrival and completion rates | **Dana + customer migration lead** | Before worker sizing | 🔴 Blocked — no measured workload |
| Forty-job incident timeline | **Dana + application engineer** | Before job-state design is finalized | 🔴 Blocked — root cause unknown |
| Data-loss and recovery tolerance | **Dana + CTO + enterprise owner** | Before production architecture sign-off | 🔴 Blocked — SLA text missing |
| Part 1 target and hard cost ceiling | **CTO / budget owner** | Before Terraform implementation | 🔴 Blocked — $400 is observed spend only |
| Residency, retention, encryption, audit, identity, tagging, and malware-scan needs | **Dana + customer security/legal owner** | Before storage/region selection | 🔴 Blocked — requirements missing |
| Architecture recommendation and implementation plan | **FDE** | After the above inputs | 🟡 Ready for review, not approval |

---

## A. Expected document traffic and processing time

This is a document-processing workload, not a traditional website benchmark.
We will size it using **contracts submitted per minute**, **contracts completed
per hour**, **how many contracts are processed at the same time**, and **how
long the oldest contract has waited**. We can derive requests per second later
if a load-testing tool needs it.

### A1. Arrival shape during migration

During the biggest customer’s migration, how many contracts will arrive:

- in the busiest **minute**?
- in the busiest **hour**?
- in a full **day**?

| Field | Detail |
|-------|--------|
| **Why we need this** | “A few thousand contracts” is total work, not how busy the system is at one moment. |
| **What decision it changes** | Worker count, memory sizing, queue depth limits, and whether inference rate limits will throttle the migration. Confirm account limits against [DigitalOcean Inference limits](https://docs.digitalocean.com/products/inference/details/limits/). |

### A2. Required completion rate

By what date must the migration finish, and how many contracts must the
platform complete in the busiest **minute** and **hour** to meet that date,
including retries?

| Field | Detail |
|-------|--------|
| **Why we need this** | The total number of contracts does not tell us how quickly capacity must clear the backlog. |
| **What decision it changes** | Number of workers, temporary migration capacity, upload pacing, and expected customer completion time. |
| **Response owner** | **Dana + customer migration lead** |
| **Blocker if unanswered** | We can show architecture, but cannot defend worker count, cost, or migration duration. |

### A3. Dump vs paced upload

Will the customer upload thousands of files **at once**, or can Halcyon **pace**
uploads over hours or days?

| Field | Detail |
|-------|--------|
| **Why we need this** | A sudden dump creates a queue spike; paced upload is cheaper and safer. |
| **What decision it changes** | Whether to pre-scale workers, add upload throttling, or negotiate a paced cutover. |

### A4. Simultaneous work and file size

How many jobs may be **processing at the same time**? What are typical, P95,
and largest PDF **sizes** and **page counts**?

| Field | Detail |
|-------|--------|
| **Why we need this** | Long PDFs use more memory and take longer (20 seconds to 4 minutes in your note). |
| **What decision it changes** | Worker RAM, concurrency per worker, and graceful-shutdown settings so deploys do not kill long jobs. See [App Platform termination](https://docs.digitalocean.com/products/app-platform/how-to/configure-termination/). |

---

## B. Investigate the 40 lost jobs before locking the fix

Please reconstruct last Tuesday’s outage as a timeline. We need to know **where
work disappeared**, not only that the box ran out of memory.

### B1. Acceptance

Were the 40 jobs accepted by the API and given **job IDs**?

### B2. Database write before queue

Was each job written to **PostgreSQL** before it was sent to **Redis/Valkey**?

### B3. Where in the queue lifecycle

Did jobs disappear:

- **before** entering Redis;
- **while waiting** in Redis;
- or **after** a worker removed / acknowledged them?

### B4. Result commit order

Were extraction results committed to PostgreSQL **before** the worker marked
the job complete?

### B5. Redis behavior under memory pressure

Was Redis configured with **persistence** and a **non-evicting** memory policy?
Did Redis restart, evict keys, or lose its volume when the Droplet ran out of
memory?

### B6. Logs still available?

Do API, worker, PostgreSQL, Redis, kernel OOM, and Docker logs still exist?
What is their timeline relative to the OOM?

### B7. Can the original PDFs be recovered?

Did PDFs live only on the failed Droplet disk, or elsewhere?

| Field | Detail |
|-------|--------|
| **Why we need this** | Distinguishes queue loss, premature “done,” database loss, and file loss — each needs a different fix. |
| **What decision it changes** | Whether PostgreSQL must be the **system of record**, how we acknowledge queue messages, and whether Spaces is mandatory for PDFs. Managed Valkey does **not** offer backup/restore — see [Valkey limits](https://docs.digitalocean.com/products/databases/valkey/details/limits/). |

---

## C. Reliability (without requiring infrastructure jargon)

Show Dana the three recovery envelopes in
[../architecture/tradeoffs-rpo-rto.md](../architecture/tradeoffs-rpo-rto.md)
before asking her to choose.

### C1. How much work can customers be asked to resend?

If the platform fails, how much **recently accepted** work could we ask a
customer to resend? (data-loss tolerance / **RPO**)

### C2. How long may the service be unavailable?

How long may uploads and processing be down? (recovery-time tolerance / **RTO**)

### C3. What does “no downtime” mean for you?

Does it mean only that customers can still **upload and check status** during a
release, or must **already-running** extraction jobs also continue without
restart?

### C4. Enterprise SLA text

What does each enterprise SLA promise, and are planned maintenance windows
excluded?

| Field | Detail |
|-------|--------|
| **Why we need this** | Reliability targets drive managed database size, redundancy, and whether cutover is allowed. |
| **What decision it changes** | Conservative vs aggressive recovery envelope, or “cutover blocked until clarified.” |

---

## D. Budget: today vs six months later

### D1. Part 1 monthly target and hard ceiling

Today you spend about **$400/month**. That is **observed spend**, not yet a
confirmed production budget. What monthly **target** and **hard ceiling** apply
for the six-week migration (platform only, and platform + inference separately)?

### D2. What “not 10×” means

“I would rather not 10× that” rejects an unexplained jump to ~$4,000/month. It
does **not** mean spending up to $4,000 is fine. Every extra dollar should map
to a **risk removed**: separate workers so one fat PDF cannot crash the API,
durable file storage, database recovery, redundancy, or monitoring.

### D3. Low / base / high estimates

We will present low/base/high Part 1 estimates and **inference usage separately**.
Please confirm whether inference tokens are inside or outside the platform
ceiling.

### D4. Part 2 $2,500 is a different conversation

The **$2,500/month** figure applies to **self-hosted models six months later**.
Is that GPU-only or total platform cost? Do **not** mix it into Part 1 sizing.

Pricing inputs (verify on the date you buy):
[App Platform](https://docs.digitalocean.com/products/app-platform/details/pricing/),
[PostgreSQL](https://docs.digitalocean.com/products/databases/postgresql/details/pricing/),
[Valkey](https://docs.digitalocean.com/products/databases/valkey/details/pricing/),
[Spaces](https://docs.digitalocean.com/products/spaces/details/pricing/),
[GPU Droplets](https://docs.digitalocean.com/products/droplets/details/pricing/).

| Field | Detail |
|-------|--------|
| **Why we need this** | Avoid overbuilding and avoid under-insuring enterprise risk. |
| **What decision it changes** | Instance sizes, HA for databases, and whether Part 2 self-hosting is feasible as stated. |

---

## E. Data handling and ownership

1. Where may contracts be stored (region / residency)?
2. How long must PDFs and extraction results be retained?
3. Who may access them (roles / customers / support)?
4. Are customer-managed encryption keys mandatory?
5. What audit records are required?
6. Who is on call when something breaks at 2 a.m.?
7. How is the **vendor / tenant identity** established at upload time
   (API key, SSO, or another IdP), and what is the expected number of vendors?
8. Confirm the tagging model: server-derived `vendor_id` on the job row,
   opaque Spaces key prefix `vendors/<vendor_uuid>/jobs/<job_uuid>/…`, and
   Spaces object metadata `vendor_id` + `job_id` (clients never supply ownership).
9. Is **malware scanning / quarantine** mandatory before inference, and which
   scanner/product must Halcyon use?
10. What are the maximum accepted PDF **bytes** and **pages**?

| Field | Detail |
|-------|--------|
| **Why we need this** | Compliance and ownership can override the recommended platform; identity and upload limits define the security boundary for the five primary requirements. |
| **What decision it changes** | Region, encryption design, access model, vendor isolation tests, quarantine gate, upload size limits, and whether App Platform is acceptable. App Platform is not PCI DSS — see [App Platform limits](https://docs.digitalocean.com/products/app-platform/details/limits/). |
| **Response owner** | **Dana + customer security/legal owner** (identity: Dana + Engineering) |
| **Blocker if unanswered** | Cannot finalize authorization, tagging, quarantine, or cutover security evidence. |

---

## F. Part 2 (six months later) — clarify the numbers

### F1. “400 concurrent users”

Does this mean 400 signed-in people, 400 active HTTP requests, or 400
**simultaneous model generations**?

### F2. “Under 2 seconds P95”

Does this mean **first visible response** (time to first token), or **all 300
output tokens completed**?

### F3. Sustained rate and burst

What sustained requests/minute and burst duration must be supported?

| Field | Detail |
|-------|--------|
| **Why we need this** | Full 300-token completion under 2s at 400 concurrent generations is likely incompatible with a $2,500 budget. |
| **What decision it changes** | GPU count, model choice (8B vs 14B), and whether to renegotiate the SLO or keep Serverless Inference as overflow. See [Part 2 design](../architecture/part2-self-hosted-inference.md). |

---

## How we will use your answers

1. Update the [assumption log](assumption-log.md) (confidence and reopen triggers).
2. Lock recovery envelope and Part 1 budget in the decision record.
3. Only then implement Terraform + simulation and produce live evidence.

Until then: **no production-ready claim** and **no DigitalOcean spend** beyond
what you explicitly authorize for experiments.
