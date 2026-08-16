<!-- SPDX-License-Identifier: MIT -->
---
id: mem-YYYY-MM-DD-slug
type: parametric
title: One-line description of the assumption being registered
summary: One or two sentences, <= 40 words, describing what is assumed known.
created: YYYY-MM-DDT00:00:00Z
updated: YYYY-MM-DDT00:00:00Z
review_after: YYYY-MM-DD
status: proposed
trust: unverified
classification: public
tags: []
links: []
supersedes: []
source: ""
spdx: MIT
---

# Title

## Assumption

What is the team assuming the model already knows from its training, without
needing a semantic note or retrieved context? Name the model/version and its
documented knowledge cutoff.

## Verified On

Date(s) this assumption was last spot-checked, and how.

## Failure Log

| Date | What was asked | What the model assumed | What was actually true | Action taken |
|------|-----------------|-------------------------|--------------------------|---------------|
| YYYY-MM-DD | ... | ... | ... | e.g. "Wrote mem-YYYY-MM-DD-... to semantic/" |

Every row here is a trigger: if the model's parametric knowledge failed,
write (or correct) a semantic note rather than continuing to rely on the
weights for that fact.

## Links

- [[mem-...]]
