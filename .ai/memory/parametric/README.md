<!-- SPDX-License-Identifier: MIT -->

# Parametric Memory

"What do we assume the model already knows?" Unlike the other four types,
this is not a per-event note store — parametric memory lives in the model's
weights, not in this repository. This folder holds a single **register**
(`register.md`) of the assumptions being made about that hidden knowledge,
plus a running log of when those assumptions failed.

- One file: `register.md`. Do not create additional per-note files here —
  add rows to the register's tables instead.
- Every failure row is a trigger to write or correct a note under
  `../semantic/` rather than continuing to rely on the model's weights for
  that fact.
- Template for the register's shape: `../templates/parametric.md`.
