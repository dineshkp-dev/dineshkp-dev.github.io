# ADR 0001 — Rebuild the resume page as a standalone HTML file with a JSON data island

Status: Accepted
Date: 2026-07-24

Amended by [ADR 0003](0003-downloadable-pdf-and-profile-photo.md): the page stays
self-contained (the profile photo is inlined as a data URI), but
`update_resume.py` now requires Windows with Word installed to export the PDF.
Its "no third-party dependencies" property is unchanged.

## Context

`index.html` was a compiled "datacomp" (`<x-dc>`) bundle: the visible page was
produced at runtime by a compressed JavaScript module unpacking an embedded
`<script type="__bundler/template">` blob. The page styling lived as inline
`style="…"` attributes and template variables (`{{ navyColor }}`, …) inside that
blob, and `update_resume.py` patched the four data arrays and contact details by
regex-matching specific inline-style strings.

We wanted a visual redesign — a strong-identity, dark-default glassmorphism
treatment — while keeping the navy/orange colour scheme, Inter + Source Serif 4
type, and the two-column layout. That is a large visual change, and the bundle
was a poor surface for it:

- It only renders through its own runtime, so edits could not be previewed with
  ordinary tools.
- Hand-editing compiled output (custom elements + `{{ }}` variables) is fragile.
- Every restyle risked breaking the updater's inline-style regexes.

## Decision

Abandon the datacomp bundle. `index.html` is now a **single, self-contained,
hand-authored** page:

- **Design** lives in one inline `<style>` block (theme tokens, glass primitive,
  layout, timeline, print, `prefers-reduced-motion`) plus a small inline
  renderer script. Dark is the committed default; a manual toggle switches to a
  light variant (persisted to `localStorage`); print forces light.
- **Data** lives in a `<script type="application/json" id="resume-data">` island.
  A vanilla-JS renderer builds the DOM from it on load. Static `<title>`/meta and
  a `<noscript>` block cover link-previews and the no-JS case.
- **`update_resume.py`** keeps its docx parser (`extract_paragraphs` /
  `parse_resume`) and now injects data by replacing the JSON island only — the
  fragile inline-style regexes are gone.

## Consequences

- Design and data are decoupled: future docx updates swap one JSON block and
  never touch markup; visual tweaks never touch the updater.
- The page renders client-side (as the old bundle did), so JS is required for the
  body; mitigated by static head metadata and a `<noscript>` fallback.
- We lose the datacomp runtime's editor niceties (the editable image slot); the
  headshot is now a "DK" monogram, swappable for a real photo later.
- Fonts load from Google Fonts (with a system-ui fallback), so the exact display
  faces need network on first load.

## Alternatives considered

- **Restyle the bundle in place** — preserves the runtime and the old updater,
  but un-previewable and regex-fragile; high risk of shipping something broken.
- **Two files (HTML shell + `resume-data.js`)** — cleanest to edit, but no longer
  a single self-contained file and prone to `file://` module/CORS quirks.
