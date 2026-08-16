<!-- SPDX-License-Identifier: MIT -->

# ROCm Contributor — Reference

Detailed rubric, templates, build/release detail, and the citation index for the
`rocm-contributor` skill. Distilled from the ROCm/TheRock repo and its shipped PR-quality skills;
this file **defers to** those sources — when they change, they win.

______________________________________________________________________

## MUST set (verbatim — non-overridable; overlays may only tighten)

- **M1** Defect-fix PRs include a regression test, or a tracked two-PR known-bug plan.
- **M2** Product-code changes carry tests, a safe-default flag, or a written waiver.
- **M3** Never disable, skip, or weaken tests solely to green CI.
- **M4** Non-trivial PRs carry work tracking (ticket, public issue, or credible no-tracker reason).
- **M5** PRs link the artifacts they relate to, and those links must resolve.

| Kind | Rules | Exception path |
| ----------------- | ---------- | --------------------------------------------------------------------- |
| Escape-hatch MUST | M2, M4, M5 | Waiver-able with an explicit written reason; reviewer decides |
| Conditional MUST | M1 | Regression test **or** a tracked two-PR plan; no bare waiver |
| Hard MUST | M3 | No waiver — there is no acceptable reason |

Source: TheRock `skills/rocm-pr-quality/reference.md`.

______________________________________________________________________

## Change classes (multiple tags allowed; pick the stricter when unsure)

`new-public-api`, `new-op/dtype/path`, `heuristic/default-selection`, `kernel/tuning`,
`build/ci`, `docs`, `revert`, `defect-fix`, `regression-test-only`, `other`.

TheRock build-repo additions (from `therock-pr-quality`): `submodule-bump`, `superbuild-cmake`,
`artifact-descriptor`, `reusable-ci`, `dependency-add`.

| Class | Typical test/flag bar |
| ----------------------------- | ------------------------------------------------------------------------------ |
| `new-public-api` | Functional/API tests; compatibility check; flag if behavior-changing |
| `new-op/dtype/path` | Tests exercising the new path across applicable devices |
| `heuristic/default-selection` | Tests + safe-default flag for the new default |
| `kernel/tuning` | Device/arch coverage for the kernel; perf evidence if perf-sensitive |
| `build/ci` | Build/CI green on supported lanes; no behavior change expected |
| `docs` | Doc/link validation only |
| `revert` | Links the reverted PR; regression test if reverting a fix |
| `defect-fix` | M1: regression test that fails pre-fix / passes post-fix, run linked |
| `submodule-bump` | State what commit/range moved and why; link upstream PR; patches still apply |
| `superbuild-cmake` | New `THEROCK_ENABLE_*` needs sane default + help string + interaction note |
| `artifact-descriptor` | One owner per component; `BUILD_TOPOLOGY.toml` stays consistent |
| `reusable-ci` | All callers updated same PR; `inputs.*`; pinned `runs-on`; logic in scripts |

______________________________________________________________________

## Finding tiers & overall assessment

| Tier | Meaning |
| --------------- | ------------------------------------------------------------------------------------------------ |
| **BLOCKING** | Correctness/security/leak, ABI/API break w/o migration, missing required tests, untested broad default-path change, incomplete cleanup of code this PR modifies. |
| **IMPORTANT** | Real behavioral risk, missing edge-case validation, meaningful test gap, missing required device/arch coverage. |
| **SUGGESTION** | Nice-to-have on code already touched: clarity, naming, small refactor, extra case. |
| **FUTURE WORK** | Out of scope; track separately; do not block. |

| Status | When |
| ------------------- | -------------------------------------------------------------------------- |
| `APPROVED` | Policy met; may carry documented, reviewer-accepted waivers. |
| `CHANGES REQUESTED` | One or more `BLOCKING` items, bad/absent tracking, defect w/o regression. |
| `REJECTED` | Fundamental problem with the approach; needs rework. |

## Risk levels (1–5)

1 = docs/metadata only · 2 = narrow, low blast radius, good coverage · 3 = core subsystem / new
feature path / schema-API / dispatch-build-test infra · 4 = broad behavior change, compat-sensitive
public API, perf-critical path, incomplete coverage · 5 = cross-project/architectural, default
behavior change in a critical path, ABI break, large unproven refactor, known unresolved failures.

______________________________________________________________________

## Test-substance smell scan (a hit is BLOCKING)

- assert-callable-only / asserts only that a mock was called
- `hasattr`-guarded bodies that silently skip
- lone `is not None` / `.called` assertions with no behavioral check
- copy-paste tests that should be parametrized
- mock-only assertions that pass against a no-op
- phantom methods/attributes not in the source (AI-slop tell)
- non-obvious tolerance/parameter choices with no recorded rationale

**Mutation question**: *what single change to the source would make this test fail?* No clear
answer → coverage padding.

**AI-generated change anti-patterns** (warrant a closer read): test sprawl; change-narrative
comments describing the diff instead of intent; "backward-compat" framing for internal-only code
(incomplete cleanup → BLOCKING); over-mocking the thing under test; excessive reformat/rename churn
mixed with a functional change; file-naming/placement drift.

______________________________________________________________________

## Waiver codes (author-declared, reviewer-adjudicated)

| Code | Use |
| ------------ | ------------------------------------------------------------------------------------------- |
| `W-DOC` | Docs/comments-only change; no product behavior. |
| `W-BUILD` | Build/CI-only change with no behavior change. |
| `W-REVERT` | Revert; the "why" is the linked reverted PR. |
| `W-HOTFIX` | Emergency fix; regression test deferred to a linked follow-up (needs named approver). |
| `W-FLAG` | New behavior landed dark behind a safe-default flag; tests/soak before enable, with tracker. |
| `W-NOTICKET` | No tracker at author time; credible reason + commitment to file & link within a window. |

Every waiver needs a one-to-two-sentence "why." A bare "N/A" is not a waiver.

## Two-PR known-bug flow (satisfies M1 without a same-PR fix)

1. **Test-only PR**: adds a regression test documenting the bug, quarantined/expected-fail and
   **tracked** (tracker id + time-box), not silently skipped.
2. **Fix PR**: lands the fix and removes the quarantine in the same PR.

______________________________________________________________________

## PR description template

```markdown
## Summary
<1-3 sentences: purpose, motivation, what this PR enables.>

## Risk Assessment
<Risk level 1-5 and a concise rationale.>

## Related
- Work tracking: <issue URL / ticket key>
- Fixes / defect: <tracker>
- Related PRs: <#PR ...>
- Design / docs: <links>

## Device / Architecture Coverage
<Blast radius + which gfx targets must be verified. State whether passing PR CI suffices,
a specific-arch run is required, or a full sweep is required, and why. Omit for docs-only.>

## Testing Summary
- <Category and what it covers.>

## Testing Checklist
- [x] <Test group> - `<command>` - Status: Passed
- [x] <Hardware test group> - `<command>` - Devices: <gfx...> - Status: Passed
- [ ] PR CI - GitHub PR checks - Status: Pending

## Flags / Guardrails
<Feature flag, default value, enable plan. "None" if N/A.>

## Adjacent Tests Considered
<What else exercises this path; what was run or why not needed.>

## Risk Acceptance / Waivers
<Waiver code + one-to-two-sentence reason + approver if required. Omit if none.>
```

Rules: `[x]` only for passed/completed; omit empty placeholder fields (no `Devices: N/A`); no
file-by-file changelogs for large PRs; follow the repo's tracker-key-in-title convention when the
policy gate requires it.

______________________________________________________________________

## Commit & branch conventions

- **PRs target `main`.** Branch names in the shared repo: `users/[USERNAME]/[name]` or
  `shared/[name]`. Long-lived: `main`, `release/*`, `compiler/amd-staging`.
- **Reviewers**: check `git log` on the touched file/folder for recent approvers; name each
  affected area's owner for cross-component changes.
- **Commit message**: concise imperative subject; body explains *why*, not what. (TheRock does
  not mandate Conventional Commits repo-wide — follow the local `git log` style and the
  `therock_pr_bot` gate, which may require a resolving `ISSUE ID` / `JIRA ID` line.)

______________________________________________________________________

## Build quick reference (CMake super-project)

```bash
# Configure + build for a GPU family (discover targets via offload-arch / rocminfo / amd-smi):
cmake -B build -GNinja . -DTHEROCK_AMDGPU_FAMILIES=gfx110X-all
cmake --build build
ctest --test-dir build        # build-integrity tests (BUILD_TESTING=ON by default)

# Rebuild-heavy work: enable ccache (fiddly flags — use the helper):
eval "$(./build_tools/setup_ccache.py)"   # Linux; Windows: for /f ... build_tools/setup_ccache.py
```

- **Required**: `-DTHEROCK_AMDGPU_FAMILIES=` or `-DTHEROCK_AMDGPU_TARGETS=` (not all are supported —
  see `therock_amdgpu_targets.cmake`).
- **Group flags** disable subsets: `-DTHEROCK_ENABLE_ALL=OFF`, `..._CORE`, `..._MATH_LIBS`,
  `..._ML_LIBS`, `..._COMM_LIBS`, `..._PROFILER`, `..._DEBUG_TOOLS`, etc. Combine with
  `-DTHEROCK_ENABLE_ALL=OFF` / `-DTHEROCK_RESET_FEATURES=ON` for a minimal build, then enable
  individual components (`-DTHEROCK_ENABLE_COMPILER=ON`, `..._HIP_RUNTIME=ON`, `..._MIOPEN=ON`, …).
- **External sources**: `-DTHEROCK_USE_EXTERNAL_<COMPONENT>=OFF` + `-DTHEROCK_<COMPONENT>_SOURCE_DIR=`.
- **Setup**: `build_tools/fetch_sources.py` fetches submodules + applies patches; `dvc` reduces
  MIOpen kernel compile time. Windows: see `docs/development/windows_support.md` (`chcp 65001`).

______________________________________________________________________

## Release strategy (CI/CD) — from `RELEASES.md`

- **CI** produces per-commit build artifacts/tarballs; **CD** produces nightly releases.
- **Multi-arch releases (current)** — one index `https://rocm.nightlies.amd.com/whl-multi-arch/`,
  select GPU with a `[device-gfx*]` pip extra; host code (`rocm-sdk-libraries`) split from
  GPU-specific `rocm-sdk-device-{target}` kernel packs (`.kpack`). Verify with `rocm-sdk test`;
  expand devel with `rocm-sdk init`.
- **Per-family releases (legacy, frozen)** — GPU-family-specific index URLs
  (`.../v2/<family>/`); superseded by multi-arch, no new per-family releases.
- **Tarballs** — flattened `/opt/rocm`-style tree; per-family or `multiarch`; reproducibility via
  `share/therock/therock_manifest.json` (TheRock commit + submodule pins + patches).
- **Native packages** — Debian (`amdrocm`, `amdrocm-core-sdk`) and RPM; currently unsigned,
  dev/test-oriented; per-arch variants (`amdrocm-gfx942`, …). WSL: `amdrocm-wsl` (DXG).
- **PyTorch / JAX** — `torch[device-gfx*]` auto-pulls matching ROCm; JAX requires ROCm installed
  first and pinning `jax` / `jax_rocm7_plugin` / `jax_rocm7_pjrt` to the same version.
- **Verify install**: Linux `rocminfo` / `amd-smi`; Windows `hipInfo.exe`.

______________________________________________________________________

## GPU architecture / device-extra matrix (subset — verify against SUPPORTED_GPUS.md)

> A `device-*` extra installing does **not** mean the runtime is functional — targets without a
> ✅ **Sanity Tested** mark in `SUPPORTED_GPUS.md` are unverified. `pip install` may succeed while
> device enumeration or kernel launch fails at runtime. File an issue if you hit one.

| Product | GFX target | Device extra / family |
| ------------------------------------------ | ---------- | --------------------- |
| Instinct MI355X / MI350X | gfx950 | `device-gfx950` |
| Instinct MI325X / MI300X / MI300A | gfx942 | `device-gfx942` |
| Instinct MI250X / MI250 / MI210 | gfx90a | `device-gfx90a` |
| Instinct MI100 | gfx908 | `device-gfx908` |
| Radeon RX 9070 / XT, AI PRO R9700 | gfx1201 | `device-gfx1201` |
| Radeon RX 9060 / XT | gfx1200 | `device-gfx1200` |
| Ryzen AI Max+ PRO 395 (Strix Halo) | gfx1151 | `device-gfx1151` |
| Radeon RX 7900 XTX / 7900 XT, W7900 | gfx1100 | `device-gfx1100` |
| Radeon RX 6900 XT / 6800 XT, W6800 | gfx1030 | `device-gfx1030` |

Discover the *authoritative* set with `offload-arch` (both OS), `rocminfo` / `amd-smi` /
`rocm_agent_enumerator` (Linux), or `hipinfo` (Windows). Do not hardcode.

______________________________________________________________________

## Engineering-lens checklist (apply every action)

**Hardware stack** — does the change respect KMD → ROCr runtime → HIP → math/ML/comm libs →
framework? Any layer it could silently break above/below?

**Generalized support** — arch-neutral host code preferred; `gfx`-specific code isolated behind
the device-code split; adding a target should be ~one more device package.

**Scalability** — holds as targets/submodules/CI lanes grow; build-time + binary-size impact
stated for new deps/components.

**Reliability** — fail fast and loud; no silent corruption; validate operations actually
succeeded; bounded timeouts on network I/O; distinguish error conditions (Python style guide).

**Verifiability** — provable by a test or a linked CI run, not assertion; reproduction evidence
for defect fixes.

**Code coverage** — lowest test level that actually fails on the regression; survives the mutation
question; no padding.

**SOLID** — single responsibility per target/module; open/closed via `THEROCK_ENABLE_*` flags and
plugins over editing core; stable ABI/API (a break without a migration path is BLOCKING);
dependency direction respects the superbuild ↔ sub-project boundary.

______________________________________________________________________

## Citation index

**Repo (public) — cite by path/line or issue number:**

- `CONTRIBUTING.md` — governance, issue tracking, PR workflow, branch naming, pre-commit, style guides.
- `RELEASES.md` — multi-arch (#3323) vs per-family, tarballs, native pkgs, PyTorch/JAX install.
- `README.md` — features, build config flags, ccache, `ctest`.
- `SUPPORTED_GPUS.md` — per-arch release readiness / Sanity Tested status.
- `docs/development/style_guides/{python,cmake,bash,github_actions}_style_guide.md`.
- `skills/rocm-pr-quality/{SKILL,reference}.md`, `skills/therock-pr-quality/SKILL.md`.
- Example living issues to model tone/handling: multi-arch rollout
  [#3323](https://github.com/ROCm/TheRock/issues/3323); wheel known-issues
  [#808](https://github.com/ROCm/TheRock/issues/808); MPI pre-install
  [#1284](https://github.com/ROCm/TheRock/issues/1284); env-var discussion
  [#1658](https://github.com/ROCm/TheRock/issues/1658); missing device-extra metadata
  [#5347](https://github.com/ROCm/TheRock/issues/5347).

> Note: this public adaptation intentionally omits any access-controlled internal
> (Confluence/JIRA) references from the source skill. When corroborating internal sources for an
> external audience, cite the public repo equivalent instead.
