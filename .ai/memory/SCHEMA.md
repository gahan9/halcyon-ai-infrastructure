<!-- SPDX-License-Identifier: MIT -->

# Memory Note Schema

> `schema_version: "1.0.0"`

Every note under `.ai/memory/{episodic,semantic,procedural,prospective}/` and
the single `.ai/memory/parametric/register.md` file carries this YAML
frontmatter. Do not add fields outside this list without bumping
`schema_version` and updating this file in the same change.

## Fields

| Field | Required | Type | Description |
|-------|----------|------|--------------|
| `id` | yes | string | `mem-YYYY-MM-DD-slug`. Matches the filename stem exactly so wikilinks resolve without an extension. |
| `type` | yes | enum | One of `episodic`, `semantic`, `procedural`, `prospective`, `parametric`. Must match the containing folder. |
| `title` | yes | string | One-line human-readable title. |
| `summary` | yes | string | <= 40 words. Loaded before the body to keep retrieval cheap — see "Token budget" in `README.md`. |
| `created` | yes | ISO 8601 datetime (UTC) | Set once, never edited. |
| `updated` | yes | ISO 8601 datetime (UTC) | Bumped on every substantive edit. |
| `review_after` | yes | ISO date | Staleness trigger. Past this date, treat the note as needing re-verification before reuse. |
| `status` | yes | enum | `draft`, `proposed`, `accepted`, `deprecated`, `superseded`. Public MADR/ADR vocabulary — see `GOVERNANCE.md`. |
| `trust` | yes | enum | `unverified`, `reviewed`, `authoritative`. See `GOVERNANCE.md` for how a note moves between levels. |
| `classification` | yes | enum | `public`, `internal`, `restricted`. This template ships and accepts only `public` seed content. |
| `tags` | yes | list of string | Lowercase, hyphenated. Used for deterministic filtering before any semantic search. |
| `links` | yes | list of string | Wikilinks to related notes, e.g. `["[[mem-2026-08-13-example]]"]`. Mirror these in the body under `## Links`. |
| `supersedes` | yes | list of string | IDs this note replaces. Empty list if none. |
| `source` | yes | string | Provenance URI, e.g. `session://...`, `meeting://...`, `skill://...`, `repo://...`. Empty string if authored directly. |
| `spdx` | yes | string | `MIT` for all first-party notes in this template. |

Optional:

| Field | Type | Description |
|-------|------|--------------|
| `confidence` | float 0-1 | Authoring/extraction confidence. Informational only — never a substitute for `trust`. |
| `owner` | string | Free-text owner/DRI. Required in practice for `prospective` notes. |

## ID convention

`mem-YYYY-MM-DD-slug` — date of authoring plus a short kebab-case slug. This
is a date-anchored identifier, not a Zettelkasten atomic ID: it is meant to
sort chronologically and stay human-readable, not to encode a hierarchy. The
filename stem must equal `id` exactly, **with one exception**: the small set
of singular, structured documents that are addressed by a stable descriptive
name rather than a per-event ID — currently `prospective/backlog.md`,
`prospective/roadmap.md`, and `parametric/register.md`. These still declare
an `id` field for frontmatter consistency, but any wikilink pointing at them
must target the actual filename stem (e.g. `[[backlog]]`, not the `id`
value) so it resolves in Obsidian.

## Minimal valid frontmatter

```yaml
---
id: mem-2026-08-13-example-note
type: semantic
title: Example note title
summary: One or two sentences, no more than 40 words, describing the content.
created: 2026-08-13T00:00:00Z
updated: 2026-08-13T00:00:00Z
review_after: 2027-02-13
status: proposed
trust: unverified
classification: public
tags: [example, template]
links: []
supersedes: []
source: ""
spdx: MIT
---
```

## Enforcement

This template does not ship a schema validator (no dependencies, no `src/`).
The `memory-curator` skill (`.ai/skills/memory-curator/SKILL.md`) checks new
or edited notes against this file by inspection before writing them. If you
later add a `src/` package to this project, a natural first test is a
frontmatter validator against this schema — see `.ai/rules/testing.md`.
