# Personal résumé page

A single, self-contained résumé web page for **Dinesh Kumar Pulikesi**, generated
from a Word résumé. The whole site is one file — `index.html` — with an
"editorial dark-glass" design (navy/orange, glassmorphism, dark default with a
light toggle).

## Repository layout

| Path | What it is |
|------|-----------|
| `index.html` | The entire site: inline CSS + a small renderer script + a JSON **data island**. Hand-authored; safe to open directly in a browser. |
| `update_resume.py` | Regenerates the data island in `index.html` from a `.docx` résumé. No third-party dependencies. |
| `docs/adr/` | Architecture Decision Records. Start with `0001-standalone-resume-rebuild.md`. |
| `CLAUDE.md` | Agent instructions (issue tracker, triage, domain docs conventions). |
| `Pulikesi_Dinesh_Kumar.docx` | Source résumé. **Git-ignored** — keep it locally, it is not committed. |

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
   This parses the docx and rewrites the `#resume-data` island in `index.html`
   **in place**. You'll see a summary like
   `Updated 7 jobs, 7 skill groups, 6 honors, 2 education entries.`
3. Open `index.html` in a browser to check it, then commit `index.html`.

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
- **Print / PDF** — the printer button (or `Ctrl/Cmd+P`) uses a print stylesheet
  that forces clean light-on-white.
- **Motion** — scroll-reveal + hover effects, automatically disabled under
  `prefers-reduced-motion`.

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

## Working conventions

- Ship changes via a **feature branch → pull request → merge** into `master`;
  don't commit directly to `master`.
- Keep the source `.docx` out of git (already in `.gitignore`).
- Record notable architectural decisions as new files under `docs/adr/`.
