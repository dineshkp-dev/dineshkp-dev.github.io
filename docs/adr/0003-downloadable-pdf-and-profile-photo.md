# ADR 0003 — Ship a downloadable PDF résumé and an embedded profile photo

Status: Accepted
Date: 2026-07-27

Amends ADR 0001 (standalone rebuild) and ADR 0002 (GitHub Pages deployment).

## Context

The page offered a **printer button** that called `window.print()`. That is not
the same thing as handing someone your résumé: it opens an OS print dialog, and
what it produces is the web page, not the Word document that recruiters and ATS
pipelines actually expect. Visitors wanting a file to keep or forward had nothing
to take away.

Separately, the identity block used a CSS `.monogram` — the initials `DK` in a
96 px circle — as a stand-in for a photograph.

Two accepted decisions constrained the fix:

- **ADR 0001** makes `index.html` a single, self-contained, hand-authored file,
  and `update_resume.py` a script with **no third-party dependencies**.
- **ADR 0002** deploys **only `index.html`** into the Pages artifact, and keeps
  the source `.docx` git-ignored and never committed.

A download link needs a file at a URL, and a photo needs image bytes. Both push
against those constraints.

## Decision

### 1. A committed PDF replaces the print button

`Dinesh-Kumar-Pulikesi-Resume.pdf` is committed to the repo and copied into
`_site/` alongside `index.html`. The printer button becomes a download link
(`<a class="ctl" download>`) in the same control cluster — an icon swap, not a new
call-to-action.

The `@media print` block **stays**. Ctrl/Cmd+P still works and still forces clean
light-on-white; only the button is gone.

The public filename is deliberately self-describing: it is what lands in a
recruiter's Downloads folder, where `index.html`-style naming would be useless.

### 2. The PDF is generated, never hand-exported

`update_resume.py` gains an `export_pdf()` step that drives Word over COM
**from PowerShell** via stdlib `subprocess` — not `pywin32`. This keeps ADR 0001's
"no third-party dependencies" property intact while removing the possibility of a
stale PDF sitting next to a fresh page.

The export **runs first and hard-fails**: if the PDF cannot be written, the script
exits non-zero and `index.html` is left untouched. Page and PDF always move
together, or neither moves.

Two details protect the user's environment, because Word is a single-instance COM
server:

- The document is exported from a **temp copy**, so an open (locked) source
  `.docx` is never a problem.
- `Visible`/`DisplayAlerts` are only set, and `Quit()` only called, when Word was
  **not** already running — otherwise the script would hide or close the user's
  own Word session.

### 3. The photo is inlined as a data URI

`profile_head_1.jpg` (1803×2253, 1.72 MB) is downscaled to a 320×320
head-and-shoulders crop at JPEG q82 — **13 KB** — and inlined as a
`data:image/jpeg;base64,…` URI in the `AVATAR` constant. `index.html` grows from
~30 KB to ~48 KB.

This preserves ADR 0001's self-contained property: the page still renders
correctly when opened directly from any folder, with no sibling files and no
network. The full-size original is git-ignored, like the `.docx`.

The photo occupies the former `.monogram` box — same 96 px circle, same 2 px
accent ring — so the layout is unchanged and the now-orphaned `initials()` helper
is removed. It is **hidden in print**, because the Word-exported PDF carries no
photo and printed output should match the file a recruiter downloads.

### 4. The website URL is parsed and rendered

The résumé header now carries `https://dineshkp-dev.github.io/`.
`update_resume.py` previously discarded it — its URL branch only recognised
`github.com` and `linkedin.com`, and the personal site is `github.io`. It is now
captured as `contact.website` and rendered as a globe row in the sidebar.

On screen this is self-referential. On **paper** it is not: a printed page has no
address bar, so the URL is the only route back to the live site.

## Consequences

- **`update_resume.py` now requires Windows with Word installed.** It is no
  longer portable to any machine with Python. Given it already reads a `.docx`
  authored in Word on a Windows-only workflow, this is an acceptable narrowing —
  but it is a real reduction in where the tool runs.
- The published site root is no longer `index.html` alone. ADR 0002's copy step
  is now an explicit two-file allowlist; adding future assets means editing it.
- Re-cropping the photo means regenerating the base64 blob; the procedure is
  recorded in the README and in a comment above the `AVATAR` constant.
- Anyone running the updater while Word has a modal dialog open will get a hard
  failure rather than a silently stale PDF. That is the intended trade.

## Alternatives considered

- **Relabel the print button "Download PDF"** with no file behind it. Zero
  pipeline change, but it is not a download — it prints the web page.
- **Commit the `.docx`** instead of a PDF. One source of truth and no drift, but
  it reverses ADR 0002's deliberate exclusion, ships Word metadata publicly, and
  hands recruiters an editable file.
- **`pywin32` for the COM export.** Cleaner Python, but adds a third-party
  dependency and breaks ADR 0001's no-dependency guarantee.
- **Generate the PDF from the page** with headless Chrome. Page and PDF could
  never disagree, but the output would be the web design rather than the
  ATS-friendly Word layout.
- **A separate `profile.jpg` file.** Keeps `index.html` small, and the workflow
  already copies a second file — but the page would break when opened without its
  sibling, losing the self-contained property.
