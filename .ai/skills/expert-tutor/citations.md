<!-- SPDX-License-Identifier: MIT -->
# Citations — where to find credible sources and how to cite them

The tutor's authority comes from grounding, not confidence. This file lists where
to find verifiable sources per domain and the rules for citing them.

## The never-fabricate rule

- **Never invent** a paper title, author, DOI, benchmark number, URL, or quote.
  If you are not sure a source exists or says what you claim, say so and point the
  learner to where to check.
- **Cite the primary source** where practical (the paper, the standard, the
  vendor doc), not a blog that summarizes it — unless the blog *is* the primary
  engineering account.
- **Link, don't lecture.** Attach a one-line takeaway and an inline hyperlink;
  do not paste long excerpts (wastes tokens, risks copyright).
- **Date-sensitive claims** (SKUs, prices, rankings, "latest version") must note
  "verify current value at <link>" — these drift.

## General academic / research

- [arXiv](https://arxiv.org/) — preprints across CS, math, physics, stat.ML.
  Note preprints may be un-peer-reviewed; say so.
- [ACM Digital Library](https://dl.acm.org/) — CS conferences/journals (SIGxxx,
  SC, ASPLOS, ...).
- [IEEE Xplore](https://ieeexplore.ieee.org/) — EE/CS/systems.
- [USENIX](https://www.usenix.org/publications/proceedings) — OSDI, NSDI, ATC,
  Security, FAST (open-access proceedings).
- [Google Scholar](https://scholar.google.com/) / [Semantic Scholar](https://www.semanticscholar.org/)
  — discovery + citation counts (impact signal, not authority).
- [DOI.org](https://www.doi.org/) — resolve a DOI to confirm a paper exists.

## CS foundations / algorithms / math

- CLRS *Introduction to Algorithms*; Sedgewick; Knuth *TAOCP* — canonical
  algorithm references.
- [Distill.pub](https://distill.pub/) — visual, rigorous ML explanations.
- [The Feynman Lectures](https://www.feynmanlectures.caltech.edu/) — physics
  intuition done well (a model for two-altitude teaching).

## GPU / HPC / systems (delegate depth to the specialist skills)

- AMD: [ROCm docs](https://rocm.docs.amd.com/),
  [GPU arch specs](https://rocm.docs.amd.com/en/latest/reference/gpu-arch-specs.html)
  — pair with the `rocm-contributor` skill.
- NVIDIA: [CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html),
  [Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
  — pair with the `cuda-contributor` skill.
- Cluster scale: ACM [Gordon Bell Prize](https://awards.acm.org/bell),
  [Top500](https://top500.org) — pair with the `cluster-ops` skill.

## Software engineering / architecture

- Martin, *Clean Code* / *Clean Architecture*; Fowler,
  [martinfowler.com](https://martinfowler.com/); Nygard, *Release It!*.
- [Google Engineering Practices](https://google.github.io/eng-practices/) and the
  [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html).
- Standards bodies: [IETF RFCs](https://www.rfc-editor.org/),
  [W3C](https://www.w3.org/TR/), [ISO](https://www.iso.org/).

## Recognized engineering blogs (primary accounts)

Acceptable when they are the primary source for a technique/incident: official
vendor engineering blogs (AWS, Google, Meta, Netflix, Cloudflare, AMD, NVIDIA),
and maintainer write-ups. Prefer these over content farms and unattributed posts.

## How to present a citation in a lesson

Inline, in the flow of the explanation:

> Tiling improves GEMM performance by raising arithmetic intensity so the kernel
> is compute- not memory-bound (see the
> [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html),
> "Memory Optimizations").

Not as a detached bibliography dump. One strong link beats five weak ones.
