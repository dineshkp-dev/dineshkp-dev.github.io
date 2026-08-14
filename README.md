# Personal résumé page

A single, self-contained résumé web page for **Dinesh Kumar Pulikesi**, generated
from a Word résumé. The whole site is one file — `index.html` — with an
"editorial dark-glass" design (navy/orange, glassmorphism, dark default with a
light toggle).

## Repository layout

| Path | What it is |
|------|-----------|
| `index.html` | The entire site: inline CSS + a small renderer script + a JSON **data island** + the profile photo, backdrop, and favicon as data URIs. Hand-authored; safe to open directly in a browser. |
| `update_resume.py` | Exports the `.docx` to PDF via Word, then regenerates the data island in `index.html`. No third-party dependencies (needs Windows + Word). |
| `Dinesh-Kumar-Pulikesi-Resume.pdf` | The downloadable résumé. **Generated — do not edit by hand.** Committed and deployed. |
| `og-card.jpg` | 1200×630 social preview card served at `og:image`. Committed and deployed; regenerate by hand (see below). |
| `docs/adr/` | Architecture Decision Records. Start with `0001-standalone-resume-rebuild.md`. |
| `CLAUDE.md` | Agent instructions (issue tracker, triage, domain docs conventions). |
| `Pulikesi_Dinesh_Kumar.docx` | Source résumé. **Git-ignored** — keep it locally, it is not committed. |
| `profile_head_1.jpg` | Source headshot. **Git-ignored** — the page ships a downscaled crop inline. |

## How it works

`index.html` is **not** a bundler artifact — it renders itself:

- **Design** lives in one inline `<style>` block plus a small vanilla-JS renderer
  at the bottom of the file.
- **Content** lives in a JSON island:
  ```html
  <script type="application/json" id="resume-data"> … </script>
  ```
  On load, the renderer reads that JSON and builds the DOM (sidebar + experience
  timeline + education + honors).

This keeps **design and data separate**: changing the résumé never touches the
markup, and restyling never touches the data.

## Update the résumé content

1. Edit your Word résumé and save it as `Pulikesi_Dinesh_Kumar.docx` in the repo
   root (this exact name is the script's default).
2. Run:
   ```bash
   python update_resume.py
   ```
   This does two things, in order:
   1. Exports the docx to `Dinesh-Kumar-Pulikesi-Resume.pdf` by driving Word over
      COM (PowerShell, via stdlib `subprocess` — no `pywin32`).
   2. Parses the docx and rewrites the `#resume-data` island in `index.html`
      **in place**.

   You'll see a summary like
   `Updated 7 jobs, 7 skill groups, 6 honors, 2 education entries.`

   The export runs **first and hard-fails**: if the PDF can't be written the
   script exits non-zero and `index.html` is left untouched, so the page and the
   downloadable PDF can never drift apart. This means the updater needs
   **Windows with Word installed**. Your open Word session is safe — the export
   works from a temp copy and won't close a Word you already had running.
3. Open `index.html` in a browser to check it, then commit **both**
   `index.html` and `Dinesh-Kumar-Pulikesi-Resume.pdf`.

Override the defaults if needed:
```bash
python update_resume.py other.docx other.html -o output.html
```

### What the parser expects

`update_resume.py` reads paragraph text straight from the `.docx` (no
`python-docx` needed) and relies on the résumé's section structure:

- Section headings: `SKILLS & HONORS`, `WORK EXPERIENCE`, `EDUCATIONAL PROFILE`.
- Each job header on its own line: `Mon. YYYY – Mon. YYYY | Company | Role`.
- Projects on their own line starting `Project:`.
- Bullets prefixed with `•`.

The parser tolerates two common Word formatting slips (it splits a `Project:`
glued onto a role, and a job header glued onto the end of a bullet), but if you
**restructure the résumé heavily, re-check the patterns** near the top of
`update_resume.py`. After any change, verify the run output counts look right and
preview the page.

## Change the design

Edit the `<style>` block or the renderer in `index.html` directly.
`update_resume.py` only rewrites the JSON island, so design edits are preserved
across content updates. Key knobs:

- **Colours / theme** — CSS custom properties under `:root[data-theme="dark"]`
  and `:root[data-theme="light"]` (accent + navy are `oklch(...)`).
- **Dark / light** — dark is the default; the moon/sun button toggles and
  remembers the choice in `localStorage`.
- **Download** — the down-arrow button links straight to
  `Dinesh-Kumar-Pulikesi-Resume.pdf`. There is no print button, but `Ctrl/Cmd+P`
  still uses the print stylesheet, which forces clean light-on-white and hides
  the photo (the PDF has none).
- **Profile photo** — inlined as a data URI in the `AVATAR` constant at the top
  of the renderer script, so the page stays self-contained. To replace it:
  crop `profile_head_1.jpg` to a square (1600 px, offset 40 px from the top),
  scale to 320×320 at JPEG q82, base64-encode it, and swap the string.
- **Backdrop** — the dark theme blurs the glass panels over a generated image,
  inlined as a WebP data URI in the `:root[data-theme="dark"] .backdrop` rule.
  A scrim above it holds text contrast, and the original gradient stays as the
  bottom layer so the page degrades gracefully if the image fails. To replace it:
  scale to 1920×1080, encode WebP q78, base64-encode, and swap the string —
  soft gradients compress to ~30 KB, so keep an eye on the size if you use a
  busier image. **Light theme deliberately keeps CSS gradients**; a bright image
  under light-mode glass wrecks legibility.
- **Favicon** — a 64×64 PNG monogram inlined as a data URI on the
  `<link rel="icon">` in `<head>`.
- **Motion** — scroll-reveal + hover effects, automatically disabled under
  `prefers-reduced-motion`.

## Social preview card

`og-card.jpg` (1200×630) is what LinkedIn, Slack, and X render when the site
link is pasted. It is **not** regenerated by `update_resume.py` — if the name,
role, or tagline changes, the card goes stale and must be rebuilt by hand.

It is composed rather than generated end-to-end: an abstract background from an
image model, with the headshot and all text composited on top with Pillow using
the page's own Inter and Source Serif 4. Text is never model-generated — see
`docs/adr/0004-social-preview-card.md`.

After replacing it, force a re-scrape: preview caches are sticky
(LinkedIn Post Inspector, Facebook Sharing Debugger).

## Preview

Just open the file — no server or build step:

```bash
# Windows
start index.html
# macOS
open index.html
# Linux
xdg-open index.html
```

Fonts (Inter + Source Serif 4) load from Google Fonts, with a system-ui
fallback if offline. The résumé body is rendered by JavaScript; a `<noscript>`
block shows contact details if JS is disabled.

## Deployment

The site is hosted on **GitHub Pages** as a user site at
**https://dineshkp-dev.github.io/**. A GitHub Actions workflow
(`.github/workflows/deploy.yml`) publishes on every push to `master`: it copies
**`index.html`, `Dinesh-Kumar-Pulikesi-Resume.pdf`, and `og-card.jpg`** into the
Pages artifact and deploys them — no build, no Jekyll. Every other source file
stays in the repo but is not served under the site URL. See
`docs/adr/0002-github-pages-deployment.md`,
`docs/adr/0003-downloadable-pdf-and-profile-photo.md`, and
`docs/adr/0004-social-preview-card.md`.

To ship a résumé update: run `python update_resume.py`, commit `index.html` and
the PDF via a PR, and merging to `master` redeploys automatically.

## Working conventions

- Ship changes via a **feature branch → pull request → merge** into `master`;
  don't commit directly to `master`.
- Keep the source `.docx` out of git (already in `.gitignore`).
- Record notable architectural decisions as new files under `docs/adr/`.
