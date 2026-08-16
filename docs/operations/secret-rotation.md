<!-- SPDX-License-Identifier: MIT -->

# Secret rotation

Rotate application secrets through the protected App Spec CI path, never
Terraform variables, local files, shell history, or logs. PostgreSQL and Valkey
use platform bindables; Spaces and inference use separate versioned JSON
secrets scoped to each runtime role.

1. Create the least-privilege replacement credential in the target environment.
2. Validate schema, environment, expiry, and role scope without printing values.
3. Inject it as an App Platform `SECRET`, deploy, and verify health and one
   authorized operation during a bounded overlap window.
4. Revoke the old credential, verify denial, and remove obsolete secret
   versions from the approved store.
5. Record owner, rotation time, affected components, and redacted evidence.

If any value appears in source, plan, state, logs, or an artifact, revoke it
immediately and treat the exposure as a security incident.
