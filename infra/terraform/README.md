<!-- SPDX-License-Identifier: MIT -->

# Terraform foundation

**Phase:** Modules and environment roots are ready for staging (already exercised)
and production *prep*. Production apply remains a reviewed, human-gated step —
see [docs/operations/production-prep.md](../../docs/operations/production-prep.md).

Do not apply production until remote state exists (`scripts/bootstrap_tf_state.sh`),
current DigitalOcean SKUs are checked, a reviewed plan is on disk, and
`CONFIRM_PRODUCTION_APPLY=yes` is set deliberately.

## Implemented foundation modules

| Module / resource | Purpose |
|-------------------|---------|
| `digitalocean_database_cluster` (PostgreSQL) | Job ledger; HA in production |
| `digitalocean_database_cluster` (Valkey) | Queue / cache |
| `digitalocean_spaces_bucket` | Private PDFs |
| `digitalocean_container_registry` | Immutable images |
| Project / VPC / bindable wiring | Least privilege, private paths, and managed-database bindables |

The App Platform application itself is deployed from the versioned App Spec by
secure CI; it is intentionally not a `digitalocean_app` resource in this design.

## Two-part Terraform design

Terraform is split into a reusable module library and thin environment
deployment roots. Environment roots call modules; they do not copy resource
logic.

### Part 1 — reusable core service library

- `modules/part1_foundation` is the public composition module for the service's
  durable infrastructure.
- Leaf modules isolate network/project, managed data, Spaces, and registry
  concerns. The App Spec deployment consumes their non-secret outputs.
- Child modules declare no backend and do not configure credentials.
- Inputs are typed service settings. Application JSON secrets are excluded.
  Provider-generated database credentials may still be state attributes and
  therefore make remote state sensitive.
- Outputs are non-sensitive resource ids, bindable names, private endpoints,
  and deployment metadata. No credential values are declared as outputs.

### Part 2 — environment deployments

- Each environment is an independent Terraform root with its own backend key,
  state, plan, approval, and provider configuration.
- `staging` and `production` call the same versioned
  `modules/part1_foundation`; environment differences are explicit inputs.
- Do not use workspaces as the only production isolation boundary.
- `.tfvars` contains non-secret sizing, region, retention, and feature flags
  only. Secret values come from the protected deployment/runtime channel.

The backend must provide encryption at rest/in transit, versioning, locking,
auditability, and separate staging/production read credentials. HCP Terraform
is one candidate; an S3-compatible backend is acceptable only after its locking
behavior is verified. Production cannot fall back to local state. Bootstrap
credentials live in protected CI and are not stored in the state they protect.

Environment database defaults:

| Environment | Managed PostgreSQL default | Reason |
|-------------|----------------------------|--------|
| Staging/exercise | 1 GiB shared single node, currently starting at ~$15/month | Lowest managed entry cost; suitable for functional and restore evidence, but explicitly not HA |
| Production | 2 GiB primary + at least one matching standby, currently starting around ~$60/month total | Managed HA/failover baseline; avoids transferring database operations to the application team |

The managed-data module keeps node size, standby count, and storage as typed
inputs. It rejects zero PostgreSQL standbys in production before apply and also
enforces the staging single-node / production HA split for Valkey.
Current prices and SKU availability remain unverified until the purchase-date
plan.

Current layout:

```
infra/terraform/
  README.md
  modules/
    part1_foundation/              # reusable infrastructure composition library
      main.tf
      variables.tf
      outputs.tf
      versions.tf
    network/
    managed_data/
    object_storage/
    registry/
  environments/
    staging/
      backend.hcl                  # backend location only; no credentials
      main.tf                     # calls ../../modules/part1_foundation
      providers.tf
      variables.tf
      staging.tfvars.example      # documented non-secret values
      versions.tf
    production/
      backend.hcl
      main.tf
      providers.tf
      variables.tf
      production.tfvars.example   # documented non-secret values
      versions.tf
```

The DOKS alternative, if ADR-001 reopens it, uses a separate
`modules/doks_platform` library and environment root. It does not add
conditional DOKS resources to `part1_foundation`.

## Runtime JSON credentials

JSON is a serialization format, **not encryption**. Application-owned plaintext
JSON secrets must never be committed, passed through `-var`, placed in
`.tfvars`, rendered in a plan, returned from an output, or deliberately stored
in Terraform state.

Terraform provider resources can expose generated database passwords or
connection attributes in state even when marked `sensitive`. Therefore remote
state is itself a secret-bearing asset: it requires encryption, locking,
versioning, least-privilege read access, audit logs, isolated staging/production
credentials, and no local-state fallback for production.

The runtime contract is:

1. Use one versioned JSON secret per integration and runtime role, not one
   all-powerful credential bundle. API and worker receive only what they need.
2. Store application JSON plaintext only in an approved CI/platform secret
   store. CI authenticates with short-lived identity where available and
   injects the secret through a protected, masked channel.
3. For Part 1, Terraform provisions foundational resources. Managed PostgreSQL
   and Valkey reach the app through DigitalOcean bindable/private connection
   variables. A separate versioned App Spec deployment job injects Spaces and
   inference JSON as App Platform `SECRET` environment values after Terraform;
   Terraform does not own those values or attempt to rotate them.
4. The App Spec deployment job is the sole owner of the App Platform app to
   avoid Terraform/App Spec drift. It reads secrets at runtime, redacts command
   output, deploys, verifies health, and discards its workspace. Rotation uses
   the same path and forces a controlled restart/deploy.
5. If ADR-001 reopens DOKS, select and approve an external secret product before
   implementation. Use its CSI/external-secret projection; base64 Kubernetes
   Secret YAML is not encryption and is never committed. This DOKS path is not
   evidence for the App Platform baseline.
6. Prefer an in-memory environment value or read-only memory-backed projection.
   If compatibility requires a file, create it at startup with mode `0600`,
   owned by the non-root process, outside persistent volumes, and remove it
   immediately after parsing.
7. Parse once into typed secret wrappers, validate schema/version and required
   fields, unwrap only at the I/O boundary, and never log the JSON, values,
   presigned URLs, or validation payload.
8. Startup gets its expected environment from platform-controlled `APP_ENV`,
   not from the JSON. It fails closed on missing, malformed, expired,
   over-privileged, or JSON/environment mismatch credentials. Rotation supports
   an overlap window and a tested restart/reload path.

Normative JSON contracts (placeholder values only):

| Secret | Consumer | Required fields |
|--------|----------|-----------------|
| `SPACES_CREDENTIALS_JSON` | API: write; worker: read | `schema_version`, `environment`, `access_key`, `secret_key` |
| `LLM_CREDENTIALS_JSON` | Worker only | `schema_version`, `environment`, `api_key` |

Database and Valkey credentials use platform bindables rather than JSON. The
placeholder shapes in [`.env.example`](../../.env.example) are the local
documentation contract; production values come only from the protected
deployment channel.

### Component credential matrix

| Component | Database | Valkey | Spaces | Inference | Provisioning token |
|-----------|----------|--------|--------|-----------|--------------------|
| API | scoped app role | enqueue/reconcile subset | write/read metadata | none | never |
| Worker | scoped worker role | claim/ack subset | read object | call model | never |
| Migration job | schema-owner role, time-bounded | none | none | none | never |
| Terraform/App deploy CI | infrastructure/app deployment identity | n/a | mints/injects scoped runtime key out of Terraform state | injects runtime key | protected CI only |

## Rules

- Pin provider versions; remote state with locking when implemented
- Pin the module source/version when environment roots consume a published
  module; local relative sources are allowed while both live in this repository
- No application JSON secrets in source, variables, plans, state, outputs, CI
  logs, or git. Treat provider-generated credentials already present in remote
  state as secrets and restrict state accordingly.
- Run formatting, validation, lint/security checks, and a reviewed plan once per
  environment root
- Scan plans for unexpected application JSON/keys before apply; audit state
  access and verify no application JSON was introduced
- Spaces is private by default. Terraform owns bucket/policy posture; a separate
  audited bootstrap/rotation step mints scoped keys and injects them only into
  components that need them
- API and worker are separate App Platform components with independent health,
  scaling, and production-disabled simulation settings
- `terraform plan` reviewed before apply; production requires a separate manual
  approval and must use the exact repository commit/module version proven in
  staging
- Prefer App Platform for Part 1 compute (ADR-001); DOKS modules only if reopen triggers fire
