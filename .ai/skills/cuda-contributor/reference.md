<!-- SPDX-License-Identifier: MIT -->

# CUDA Contributor — Reference

Detailed rubric, templates, build/test detail, compute-capability matrix, and the citation index for
the `cuda-contributor` skill. Distilled from the `NVIDIA/cuda-samples` repo, the wider NVIDIA org,
and the official [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html);
this file **defers to** those sources — when they change, they win.

______________________________________________________________________

## MUST set (this skill's synthesized merge floor; the target repo's `CONTRIBUTING.md` wins)

- **M1** Defect-fix PRs demonstrate fail→pass (repro that fails pre-fix, passes post-fix).
- **M2** New/changed sample/kernel builds clean under `nvcc` for the declared arch set and runs to a
  correct result; behavior-changing library/API code carries a test or a written waiver.
- **M3** Never disable, `"skip"`, or weaken a sample/test solely to green CI.
- **M4** Non-trivial PRs carry work tracking (issue link, or credible no-tracker reason).
- **M5** PRs link the artifacts/issues they relate to, and those links must resolve.

| Kind | Rules | Exception path |
| ----------------- | ---------- | --------------------------------------------------------------------- |
| Escape-hatch MUST | M2, M4, M5 | Waiver-able with an explicit written reason; reviewer decides |
| Conditional MUST | M1 | Fail→pass evidence **or** a tracked two-PR plan; no bare waiver |
| Hard MUST | M3 | No waiver — there is no acceptable reason |

> Unlike ROCm/TheRock (which ships an in-repo `rocm-pr-quality` skill), cuda-samples ships no formal
> PR-quality rubric. The M-set above is this skill's synthesis; when a target NVIDIA repo publishes
> its own contribution/PR policy, that policy is authoritative.

______________________________________________________________________

## Change classes (multiple tags allowed; pick the stricter when unsure)

`new-sample`, `new-public-api`, `new-op/dtype/path`, `kernel/tuning`, `arch-specific-path`,
`build/cmake`, `ci`, `docs`, `revert`, `defect-fix`, `python-sample`, `common-helper`, `other`.

| Class | Typical test/flag bar |
| --------------------- | ------------------------------------------------------------------------------ |
| `new-sample` | Builds clean; runs to correct output; `test_args.json` entry if CLI args needed |
| `new-public-api` | Functional/API tests; compatibility note; guard if behavior-changing |
| `new-op/dtype/path` | Runs exercising the new path across applicable compute capabilities |
| `kernel/tuning` | Arch coverage for the kernel; perf evidence (before/after) if perf-sensitive |
| `arch-specific-path` | `__CUDA_ARCH__` / capability guard + fallback; declared `-gencode` set |
| `build/cmake` | Configure+build green on supported generators/platforms; no behavior change |
| `ci` | Workflow green; callers updated; logic in scripts not inline YAML |
| `docs` | Doc/link validation only |
| `revert` | Links the reverted PR; repro if reverting a fix |
| `defect-fix` | M1: fail→pass evidence, run/output linked |
| `python-sample` | Runs in Python 3.10+ env with pinned `requirements.txt`; documents output |
| `common-helper` | All dependent samples still build/run; no destructive break of shared code |

______________________________________________________________________

## Finding tiers & overall assessment

| Tier | Meaning |
| --------------- | ------------------------------------------------------------------------------------------------ |
| **BLOCKING** | Correctness/security/leak, unchecked CUDA call on a critical path, data race, ABI/API break w/o migration, missing required proof, weakened/skipped test, incomplete cleanup of code this PR modifies. |
| **IMPORTANT** | Real behavioral risk, missing edge-case validation, meaningful test gap, missing required arch/capability coverage. |
| **SUGGESTION** | Nice-to-have on code already touched: clarity, naming, small refactor, extra case. |
| **FUTURE WORK** | Out of scope; track separately; do not block. |

| Status | When |
| ------------------- | -------------------------------------------------------------------------- |
| `APPROVED` | Policy met; may carry documented, reviewer-accepted waivers. |
| `CHANGES REQUESTED` | One or more `BLOCKING` items, bad/absent tracking, defect w/o repro. |
| `REJECTED` | Fundamental problem with the approach; needs rework. |

## Risk levels (1–5)

1 = docs/metadata only · 2 = narrow, low blast radius, good coverage · 3 = core sample / new feature
path / shared `Common/` helper / build infra · 4 = broad behavior change, compat-sensitive public API,
perf-critical kernel, incomplete coverage · 5 = cross-project/architectural, default behavior change
in a critical path, ABI break, large unproven refactor, known unresolved failures.

______________________________________________________________________

## Test-substance smell scan (a hit is BLOCKING)

- "runs to completion" with no correctness/reference check (exit code 0 is not verification)
- error paths swallowed: CUDA API returns ignored, no `cudaGetLastError()` after a launch
- `__syncthreads()` / stream / event ordering asserted by comment, not by result
- copy-paste sample logic that should reuse a `Common/` helper
- non-obvious tolerance / grid-block-dim choices with no recorded rationale
- phantom API calls or flags not present in the CUDA Toolkit version in use (AI-slop tell)

**Mutation question**: *what single change to the source would this test/sample still pass silently?*
No clear answer → coverage padding.

**AI-generated change anti-patterns** (warrant a closer read): sample sprawl; change-narrative
comments describing the diff instead of intent; "backward-compat" framing for a self-contained
sample (incomplete cleanup → BLOCKING); over-mocking the thing under test; excessive
reformat/rename churn mixed with a functional change; file-naming/category placement drift.

______________________________________________________________________

## Waiver codes (author-declared, reviewer-adjudicated)

| Code | Use |
| ------------ | ------------------------------------------------------------------------------------------- |
| `W-DOC` | Docs/comments-only change; no product behavior. |
| `W-BUILD` | Build/CI-only change with no behavior change. |
| `W-REVERT` | Revert; the "why" is the linked reverted PR. |
| `W-HWLIMIT` | Cannot run on required arch/capability at author time; needs a named approver + follow-up. |
| `W-GUARD` | New arch-specific path landed behind a capability guard with a correct fallback. |
| `W-NOTICKET` | No tracker at author time; credible reason + commitment to file & link within a window. |

Every waiver needs a one-to-two-sentence "why." A bare "N/A" is not a waiver.

## Two-PR known-bug flow (satisfies M1 without a same-PR fix)

1. **Repro/issue PR**: documents the failing case (issue + minimal repro), tracked and time-boxed.
2. **Fix PR**: lands the fix and links the repro; shows the case now passing.

______________________________________________________________________

## PR description template

```markdown
## Summary
<1-3 sentences: purpose, motivation, what this PR enables.>

## Risk Assessment
<Risk level 1-5 and a concise rationale.>

## Related
- Work tracking: <issue URL>
- Fixes / defect: <issue>
- Related PRs: <#PR ...>
- Docs / Programming Guide section: <links>

## Architecture / Compute-Capability Coverage
<Blast radius + which SM targets / compute capabilities were built and run. State whether a clean
build + sample run suffices, a specific-arch run is required, or a broader sweep is required, and
why. Omit for docs-only.>

## Testing Summary
- <What was built (nvcc arch set) and run (sample / run_tests.py), and the result.>

## Testing Checklist
- [x] Build - `cmake .. && make -j` - Status: Passed
- [x] Sample run - `run_tests.py --dir ./build/cpp --config test_args.json` - Status: Passed
- [ ] PR CI - GitHub PR checks - Status: Pending

## Flags / Guardrails
<Capability guard, CMake option, default value, enable plan. "None" if N/A.>

## Adjacent Samples Considered
<What else exercises this path (shared Common/ helper, sibling sample); what was run or why not.>

## Risk Acceptance / Waivers
<Waiver code + one-to-two-sentence reason + approver if required. Omit if none.>
```

Rules: `[x]` only for passed/completed; omit empty placeholder fields; no file-by-file changelogs
for large PRs; follow Conventional Comments in review threads; PRs target `master`.

______________________________________________________________________

## Commit & branch conventions

- **Fork-based workflow.** Feature branch: `git checkout -b your-feature-branch`; PRs target `master`.
- **Reviewers** are auto-assigned by maintainers on cuda-samples; for other NVIDIA repos, check
  `git log` / CODEOWNERS on the touched path.
- **Commit message**: concise imperative subject; body explains *why*, not what. cuda-samples does
  not mandate Conventional Commits. (This template project's own `git-commits` rule additionally
  requires a `Signed-off-by:` trailer for commits *in this repo* — that is a local rule, not a
  cuda-samples requirement.)

______________________________________________________________________

## Build & test quick reference (CMake)

```bash
# Linux configure + build:
mkdir build && cd build
cmake ..                       # CMake >= 3.20
make -j$(nproc)

# On-device debugging (adds nvcc -G; perf cost, off by default):
cmake -DENABLE_CUDA_DEBUG=True ..

# Tegra / platform-specific samples:
cmake -DBUILD_TEGRA=True ..

# aarch64 Linux cross-compile:
cmake .. -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/toolchain-aarch64-linux.cmake \
         -DTARGET_FS=/path/to/target/rootfs

# QNX cross-compile (CUDA 13.0+):
QNX_HOST=... QNX_TARGET=... cmake .. -DBUILD_TEGRA=True \
  -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/toolchain-aarch64-qnx.cmake

# Forward compatibility (new Toolkit/UMD, old KMD): point at the driver stubs
cmake -DCMAKE_PREFIX_PATH=/usr/local/cuda/lib64/stubs/ ..

# Sanity-run all built samples (NOT a validation/benchmark suite):
cd .. && python3 run_tests.py --dir ./build/cpp --config test_args.json --output ./test
```

- **Windows**: VS 2019 16.5+ CMake support, or `cmake .. -G "Visual Studio 16 2019" -A x64`, then
  build `CUDA_Samples.sln` / `cmake --build . --config Release` and `cmake --install .`.
- **Install layout**: `build/bin/${TARGET_ARCH}/${TARGET_OS}/${BUILD_TYPE}` (override with
  `CMAKE_INSTALL_PREFIX` or `CUDA_SAMPLES_INSTALL_DIR`).
- **`test_args.json` modes**: `"skip": true` (display/graphical samples), single `"args": [...]`,
  or multiple `"runs": [{ "args": [...] }, ...]`. `run_tests.py` returns the first non-zero code and
  prints a failed-runs summary; logs land in `--output` as `APM_<name>.txt`.
- **Python samples**: not built by top-level CMake. Per sample: `cd python/<Category>/<sample>`,
  `pip install -r requirements.txt` (Python 3.10+, matching Toolkit), `python <script>.py`.

______________________________________________________________________

## Repository structure (cuda-samples)

- `cpp/` — C++/CUDA samples in numbered categories:
  `0_Introduction`, `1_Utilities`, `2_Concepts_and_Techniques`, `3_CUDA_Features`,
  `4_CUDA_Libraries`, `5_Domain_Specific`, `6_Performance`, `7_libNVVM`, `8_Platform_Specific`,
  `9_CUDA_Tile`.
- `python/` — `cuda.core`-focused samples: `1_GettingStarted`, `2_CoreConcepts`,
  `3_FrameworkInterop`, `4_DistributedComputing`, `Utilities`.
- `Common/` — shared C++/CUDA helper headers reused across samples.
- `cmake/` (incl. `toolchains/`), `bin/win64/`, `.clang-format`, `.pre-commit-config.yaml`,
  `CMakeLists.txt`, `run_tests.py`, `test_args.json`, `CHANGELOG.md`.

______________________________________________________________________

## Compute-capability / architecture matrix (subset — verify with `deviceQuery` + Programming Guide)

> Discover the *authoritative* capability of the device in hand with the `deviceQuery` sample or
> `nvidia-smi`; confirm supported features against the CUDA Programming Guide "Compute Capabilities"
> appendix. Do not hardcode an arch the change has not been built and run for. Ship PTX
> (`compute_XX`) for forward-compatible JIT alongside SASS (`sm_XX`) where practical.

| Architecture | Compute capability (SM) | `-gencode` (typical) |
| --------------------- | ----------------------- | ------------------------------------- |
| Pascal | 6.0 / 6.1 | `arch=compute_60,code=sm_60` |
| Volta | 7.0 | `arch=compute_70,code=sm_70` |
| Turing | 7.5 | `arch=compute_75,code=sm_75` |
| Ampere | 8.0 / 8.6 / 8.7 | `arch=compute_80,code=sm_80` |
| Ada Lovelace | 8.9 | `arch=compute_89,code=sm_89` |
| Hopper | 9.0 | `arch=compute_90,code=sm_90` |
| Blackwell | 10.x / 12.x | `arch=compute_100,code=sm_100` (verify)|

Feature gates to remember (confirm against the Programming Guide for the target Toolkit): Cooperative
Groups / stream priorities need SM ≥ 3.5; multi-block Cooperative Groups need Pascal+; tensor cores
need Volta+ (shapes/dtypes vary by arch); TMA / thread-block clusters are Hopper+.

______________________________________________________________________

## Engineering-lens checklist (apply every action)

**Hardware stack** — does the change respect KMD → CUDA driver API → CUDA runtime → math/DL libs
(cuBLAS/cuFFT/cuDNN/…) → framework? Any layer it could silently break above/below?

**Generalized support** — arch-neutral device code preferred; capability-specific code isolated
behind `__CUDA_ARCH__` guards with a correct fallback; PTX shipped for forward-compatible JIT.

**Scalability** — holds as SM targets / samples / CI lanes grow; build-time + fat-binary size impact
stated for new `-gencode`s or deps.

**Reliability** — every CUDA API return checked; `cudaGetLastError()` after launches; fail fast and
loud; correct stream/event synchronization; no leaked device memory/streams on error paths; bounded
timeouts on host I/O.

**Verifiability** — provable by a build+run or a linked CI run, not assertion; repro evidence for
defect fixes.

**Code coverage** — lowest test level that actually catches the regression; survives the mutation
question; no padding.

**SOLID** — single responsibility per sample/module; open/closed via new samples/options over
destructive edits to shared `Common/` code; stable public API/ABI (a break without a migration path
is BLOCKING); dependency direction respects the sample ↔ `Common/` boundary.

______________________________________________________________________

## Citation index

**Repos (public) — cite by path/line, issue, or PR number:**

- [`NVIDIA/cuda-samples`](https://github.com/NVIDIA/cuda-samples) — `README.md` (build/test/install,
  samples list, dependencies, `run_tests.py`), `CONTRIBUTING.md` (fork→PR to `master`, pre-commit,
  Google C++ Style Guide, Conventional Comments), `.pre-commit-config.yaml`, `.clang-format`,
  `test_args.json`, `cmake/toolchains/`. Current release line: CUDA Toolkit 13.x.
- Wider org: [`NVIDIA`](https://github.com/NVIDIA) — `CCCL`, `CUTLASS`, `TensorRT-LLM`, `warp`,
  `Megatron-LM`, `open-gpu-kernel-modules` (each has its own `CONTRIBUTING.md`; verify policy).

**Official documentation (authoritative for API/GPU correctness):**

- [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html) —
  programming model, memory model, execution model, Compute Capabilities appendix, CUDA features
  (graphs, cooperative groups, unified memory, async copies, IPC, virtual memory management).
- [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html).
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html);
  [Conventional Comments](https://conventionalcomments.org/).

> Note: cuda-samples' README currently states public contributions are not being accepted even as its
> `CONTRIBUTING.md` documents a fork→PR flow. Always re-verify the live policy in the target repo
> before advising a PR, and prefer a sibling NVIDIA repo that accepts community PRs when it is closed.
