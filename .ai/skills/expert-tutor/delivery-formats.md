<!-- SPDX-License-Identifier: MIT -->
# Delivery Formats — the multi-modal output playbook

Every module can be delivered in more than one medium. The default is text +
mermaid; richer formats are offered via `AskQuestion` at workflow gate 4 and
whenever a module is visual-heavy. **Non-negotiable: every artifact ships with an
editable source the learner can change and regenerate — never a locked export.**

## The format menu (what to ask the learner)

Use the `AskQuestion` tool with options roughly like:

- Quick + clear (text + a mermaid diagram) — the default, cheapest.
- Interactive canvas / mini-site (explore it beside the chat).
- Slides (a deck I can present / edit).
- Image / illustration (a picture of the concept).
- Video (an editable storyboard I can narrate).

Allow multiple selections. If the learner is neutral, pick the default and offer
to upgrade.

## 1. Mermaid diagrams (default)

- Use for flow, sequence, state, class, ER, and mindmap views embedded in chat or
  a module file.
- The fenced mermaid block **is** the editable source — the learner edits text,
  the diagram re-renders.
- Follow safe mermaid syntax: no spaces in node IDs (use camelCase); quote labels
  containing parentheses/colons; avoid reserved IDs (`end`, `graph`); do not set
  explicit colors (breaks dark mode). Prefer one clear diagram over a dense one.

## 2. Interactive canvas / mini-site

- **When:** the learner wants to *interact* — step through an algorithm, drag a
  slider to see an effect, explore labeled charts/timelines, or view a drawing
  that benefits from layout.
- **How:** read and follow the Cursor `canvas` skill, then write exactly one
  `.canvas.tsx` file to the managed `canvases/` directory. Import only from
  `cursor/canvas`; embed all data inline (no `fetch`); label every plot (title,
  axis + units, legend, source). Never render empty/placeholder states.
- **Editable source:** the `.canvas.tsx` file itself — the learner (or the tutor
  on request) edits the component and it recompiles live.
- **Good uses:** an interactive tiled-GEMM visualizer, a step-through of a sorting
  algorithm, a parameter-sweep chart, a concept map with expandable nodes.

## 3. Slides

- **When:** the learner wants something presentable — a lesson deck, a summary to
  share, a talk.
- **How:** invoke `slide-creator` to produce a self-contained `.pptx` with the
  source data embedded for round-trip refinement; style with `theme-factory`
  (offer a theme, or match an existing brand such as AMD Instinct if relevant).
- **Editable source:** the `.pptx` plus its embedded source data — the learner
  edits content and re-renders; no baked-flat images without the underlying text.
- **Guardrail:** slide generation is token-heavy — confirm scope (how many
  slides, which modules) before building.

## 4. Images / illustrations

- **When:** a single concept image, diagram render, or piece of concept art
  clarifies faster than words (e.g. "show me a memory-hierarchy pyramid").
- **How:** use the `GenerateImage` tool with a concrete description (subject,
  layout, style, labels, aspect ratio). Do NOT use image generation for
  data-heavy charts/plots — those belong in a canvas or a mermaid diagram.
- **Editable source:** keep the text prompt (and any mermaid/spec it was derived
  from) alongside the image so the learner can tweak and regenerate.

## 5. Video

- **Reality check:** there is no native video-generation tool in this
  environment. Do not promise a rendered `.mp4`.
- **What to deliver instead:** an **editable storyboard** — numbered scenes, each
  with on-screen visual (a mermaid frame, an image prompt, or a canvas state),
  narration script, and duration. Optionally animate the sequence in a canvas
  (stepper / auto-play) for a video-like experience.
- **Editable source:** the storyboard document (scenes + script). The learner can
  edit any scene, and hand the script to an external TTS/video tool if they want a
  rendered file.
- **Guardrail:** confirm scope before producing — storyboards are effort-heavy.

## Editable-source checklist (apply to every artifact)

- [ ] The learner can change the content and re-render (text, `.canvas.tsx`,
      `.pptx` source data, image prompt, or storyboard script is provided).
- [ ] No secrets, credentials, or `confidential`/`secret` data embedded.
- [ ] Charts/tables are self-describing (title, units, legend, source).
- [ ] The cheaper default (mermaid) was offered when the learner was neutral.
- [ ] Token cost of a heavy artifact was flagged before building.
