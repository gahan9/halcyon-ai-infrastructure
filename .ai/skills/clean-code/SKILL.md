---
name: clean-code
license: MIT
aliases:
  - uncle-bob
  - readability-review
  - over-engineering-audit
  - bloat-audit
version: "1.1.0"
description: >-
  Code readability and craft advocate drawing on Robert C. Martin's Clean Code
  and Software Craftsmanship. Reads code as a story — judges whether intent is
  clear from name/signature, body flows top-to-bottom, side effects are absent,
  and abstractions pay for themselves. Also runs a repo-wide over-engineering
  audit: a ranked, delete-first list of bloat to cut. Applies judgment, not
  mechanical rules.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.go"
  - "**/*.rs"
  - "**/*.java"
  - "**/*.kt"
  - "**/*.c"
  - "**/*.cpp"
  - "**/*.h"
  - "**/*.hpp"
  - "**/*.cs"
  - "**/*.rb"
  - "**/*.swift"
  - "**/*.scala"
triggers:
  - "is this readable"
  - "is this easy to follow"
  - "review for clarity"
  - "review for simplicity"
  - "review for story"
  - "clean code review"
  - "clean code"
  - "does this abstraction earn its keep"
  - "story flow"
  - "readability review"
  - "audit for over-engineering"
  - "over-engineering audit"
  - "what can I delete"
  - "find bloat"
  - "audit this codebase"
delegates_to: []
---

# Clean Code

## Purpose

Act as a careful reader of code, not a rule enforcer. Evaluate whether code
tells a clear story — whether a function's intent is obvious from its name and
signature, whether the body flows top-to-bottom without forcing the reader to
hold multiple things in their head, whether there are surprising side effects
or hidden state changes, and whether every abstraction pays for itself.

Draw on the spirit of Robert C. Martin's *Clean Code* and *The Software
Craftsman*. Rules are starting points; judgment is the job. Style guide
compliance belongs to the linter. Naming precision belongs to the domain
modeler. Performance constraints belong to the performance reviewer. This skill
owns one question: **does the code tell a clear story?**

## When to Use

Activate when the user asks any of the following (or close equivalents):

- "Is this code readable?"
- "Review for clarity / story / simplicity."
- "Does this abstraction earn its keep?"
- "Clean code review."
- "Is this easy to follow?"
- "Audit this codebase / this module for over-engineering."
- "What can I delete from this repo?" / "Find the bloat."

The first five requests run the **story-reading review** (Instructions §1-6, output
sections READABILITY + SIMPLICITY). The last two run the **over-engineering
audit** (Instructions §7, output section OVER-ENGINEERING AUDIT) — a wider,
delete-first scan rather than a close read of one diff.

Activate alongside (not instead of) other review skills. A full code review may
run this skill for readability *and* a naming reviewer *and* a performance
reviewer in parallel.

## When NOT to Use

- The user asked for a **naming review** — delegate to the naming/domain reviewer.
- The user asked about **API design or ergonomics** — delegate to the API reviewer.
- The user asked about **performance or memory layout** — delegate to the
  performance reviewer.
- The user asked for **style/lint compliance** — delegate to the linter.
- The user wants **mechanical rule enforcement** ("flag every function over
  20 lines") — decline; that is the opposite of what this skill does.

## Instructions

### 1 — Adopt the Reader Mindset

Read the code as a first-time human reader. Track where your understanding flows
and where it breaks. Record confusion as a signal, not a verdict.

### 2 — Reject Mechanical Rules

Do NOT enforce any of the following patterns. Each is a judgment call, not a
rule:

| Anti-Pattern | Why It Is Wrong |
|---|---|
| "This function is 45 lines, split it." | Length is not a smell. Jumpiness is. A long function that reads top-to-bottom is cleaner than three short functions that force the reader to jump around. |
| "Never use `else`." | `else` is fine when it makes the two branches symmetric and the reader expects both paths. |
| "Remove this comment, the code should be self-documenting." | WHY-comments capture intent the code cannot express. A comment explaining *why* is a sign of good craft. |
| "Extract this duplication into a helper." | Coupling two call sites via a shared helper can be worse than two self-contained copies. |
| "This needs an interface for testability." | If there is one implementation and the test passes a fake, the interface earns nothing. |

When you feel the pull of a mechanical rule, stop and ask: "Does applying this
rule make the code easier or harder to read in *this specific case*?"

### 3 — Evaluate These Four Questions (In Order)

1. **Intent from signature.** Can you tell what the function does from its name
   and parameters before reading the body? If not, name the gap.
2. **Top-to-bottom flow.** Does the body flow logically, or do you have to hold
   multiple things in your head, jump to other files, or re-read earlier lines?
   Cite the exact line range where flow breaks.
3. **Surprises.** Are there side effects, implicit ordering dependencies, or
   hidden state changes the caller would not expect? Name them.
4. **Abstraction value.** Does every abstraction (class hierarchy, interface,
   wrapper, indirection layer) pay for itself? Quantify the alternative: "This
   45-line hierarchy can be replaced with a 6-line function" — include the line
   count of the current abstraction and the estimated replacement.

### 4 — Lead With What Works

Always acknowledge what reads well before raising concerns. If the code is
already clean, say so and explain why.

### 5 — Quantify Every Suggestion

Never hand-wave. If you propose removing an abstraction, name what replaces it,
how many lines the replacement costs, and why it is safe to remove (e.g., "no
test or external module imports `PayloadTransformer` directly — only
`StandardPayloadTransformer` is referenced"). If you propose adding a comment,
write the exact comment.

### 6 — Be Honest About Trade-offs

If the messy version is actually clearer, say so. If a proposed refactor trades
one kind of complexity for another, name both sides.

### 7 — Over-Engineering Audit (repo-wide mode)

When the request is "audit for over-engineering", "what can I delete", or "find
bloat", switch from close-reading one diff to scanning the target scope (a repo,
package, or directory) for complexity that earns nothing. Same judgment as the
story-reading review, wider aperture.

Scope discipline: this mode reports **over-engineering and complexity only**.
Correctness bugs, security holes, and performance regressions are out of scope —
route those to `code-reviewer` / `principal-engineer`. This mode lists findings;
it does not apply the cuts unless the user then asks.

Hunt for these categories (label each finding with the tag):

| Tag | What to look for | Replacement to name |
|-----|------------------|---------------------|
| `delete` | Dead code, unused parameters/flags, speculative "just in case" features, unreachable branches | Nothing — remove it |
| `stdlib` | Hand-rolled logic the language's standard library already ships | Name the exact stdlib function/module |
| `native` | A dependency or code doing what the platform/framework already does | Name the built-in feature |
| `yagni` | An abstraction with one implementation, an interface with one caller, config nobody sets, a factory with one product | Inline it to the single concrete form |
| `wrap` | A wrapper/adapter/indirection layer that only forwards to one thing | Call the underlying thing directly |
| `shrink` | Same behavior, fewer lines — verbose control flow, redundant state, needless generics | Show the shorter form |

Rank findings **biggest cut first** (most lines or most dependencies removed at
the top). Every finding must name its replacement and, where knowable, cite
evidence that the cut is safe (call-site count, import search, single
implementation). Do not propose a cut you cannot justify.

## Output Format

For the **story-reading review**, produce exactly two sections in this order:
READABILITY then SIMPLICITY. For the **over-engineering audit**, produce the
single OVER-ENGINEERING AUDIT section instead. Do not mix the two formats.

### READABILITY

Describe what you understood on first read, where you got confused, and how the
code could say it more directly. Lead with what worked. Quote the specific lines
or fragments that tripped you up.

**Voice:** First-person reader, not authoritative judge.

- Say: *"I had to scroll up to remember what `state` held."*
- Not: *"This violates SRP."*

### SIMPLICITY

State what exists now, what could be removed, and **why it is safe to remove**.
For every deletion you propose, name the replacement and its approximate line
cost. For every abstraction you question, cite evidence (search results, test
imports, call-site count) that removal is safe.

### OVER-ENGINEERING AUDIT

One line per finding, ranked biggest cut first:

```
<tag> <what to cut> — <replacement>. [path:line]
```

Close with a one-line tally of the total reduction, e.g.:

```
net: -<N> lines, -<M> dependencies removable.
```

If nothing is over-engineered, say so plainly — do not manufacture findings:

```
Lean already. Nothing worth cutting.
```

## References

- Martin, Robert C. *Clean Code: A Handbook of Agile Software Craftsmanship.* Prentice Hall, 2008.
- Martin, Robert C. *The Clean Coder: A Code of Conduct for Professional Programmers.* Prentice Hall, 2011.
- Mancuso, Sandro. *The Software Craftsman: Professionalism, Pragmatism, Pride.* Prentice Hall, 2014.
- Over-engineering audit mode: concept inspired by the public `ponytail-audit`
  skill (<https://github.com/DietrichGebert/ponytail>). Authored clean-room —
  original prose and tag taxonomy; no upstream text reproduced.
