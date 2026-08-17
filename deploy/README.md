<!-- SPDX-License-Identifier: MIT -->

# Deploy artifacts (App Platform, CI-owned)

Terraform provisions foundations only; this directory owns the App Spec.

| File | Purpose |
|------|---------|
| `app-spec.staging.yaml` | Versioned staging App Spec (placeholders + `SECRET` keys) |
| `app-spec.production.yaml` | Production template — do not apply without approvals |

For local or App Platform deployment, inject these secrets through a
gitignored `.env` or App Platform `SECRET` values:

- `DATABASE_URL` — `doctl databases connection $HALCYON_POSTGRES_ID`
- `VALKEY_URL` — `doctl databases connection $HALCYON_VALKEY_ID`
- `SPACES_CREDENTIALS_JSON` — Spaces access/secret JSON matching `APP_ENV`
- `LLM_CREDENTIALS_JSON` — only if leaving fake inference

See `docs/operations/secret-rotation.md` for App Platform `SECRET` injection.
