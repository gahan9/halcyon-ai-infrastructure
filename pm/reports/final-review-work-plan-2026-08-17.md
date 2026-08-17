<!-- SPDX-License-Identifier: MIT -->

# Final submission review work plan — 2026-08-17

## Decision

P0 documentation fixes are in the working tree. Do not send until those changes
are merged to the default branch and the dirty production-prep diff is reviewed.

## Review status

- **Recommendation — unblocked after merge:** Updated to reflect built staging
  smoke; trimmed assumptions/glossary; six-week plan refreshed. Verify rendered
  page count (target two to four pages) before send.
- **Repository — blocked:** Application, infrastructure, deployment, tests, and
  demo script exist. Unreviewed, uncommitted production-prep changes remain.
- **Live endpoint — available with qualification:** Public staging responds;
  FakeAuth documented in `docs/evidence/access.md`.
- **Verification — partial:** 60 tests passed locally; Locust smoke only; seven
  production-readiness gates remain FAIL.

## Final review sequence

### 1. Make the recommendation the authoritative deliverable

Owner: author. **Done in working tree** — merge before send.

1. Updated `docs/recommendation/dana-recommendation.md`.
2. Render and verify two-to-four pages.
3. Confirm no production-ready overclaim.

### 2. Freeze and review the repository evidence

Owner: engineering. Confidence: medium because the working tree is not clean.

1. Review the current modified and untracked files as one production-preparation
   change; split it if the pull-request review budget is exceeded.
2. Ensure `.env`, Terraform state, filled App Specs, tokens, and credentials
   are absent; run the repository secret and dependency checks.
3. Run blocking application lint, format, strict typing, tests, Terraform
   validation, and image build.
4. Commit through a signed-off pull request, merge it, and confirm the public
   default branch is clean and CI is green.

Exit: the public repository link resolves to the exact reviewed evidence being
submitted.

### 3. Update the reviewer path

Owner: author. **Done in working tree** — merge before send.

1. Updated root README and added `docs/evidence/access.md`.
2. Verify links from an unauthenticated browser session.

Exit: a reviewer can find all three requested deliverables from the README in
under two minutes.

### 4. Perform the send/no-send review

Owner: author plus one independent reviewer. Confidence: high after steps 1–3.

1. Read the recommendation as Dana, not as an implementer.
2. Confirm the rendered page count and opening recommendation.
3. Open the repository, recommendation, staging notes, and live endpoint from
   the exact email links.
4. Confirm the email makes no claim stronger than the evidence.
5. Send only after the default branch contains the final documents and all
   required access works.

## Send criteria

Send when all are true:

- the recommendation is current and renders to two to four pages;
- the default branch contains the reviewed application, infrastructure, and
  demonstration evidence;
- CI is green and the working tree used for submission is clean;
- the live endpoint is reachable and its exercise limitations are disclosed;
- repository and documentation links work without local files or secrets.

