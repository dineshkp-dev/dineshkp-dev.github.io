# ADR 0002 — Deploy the resume page to GitHub Pages via GitHub Actions

Status: Accepted
Date: 2026-07-25

## Context

`index.html` is a single, self-contained static page (see ADR 0001) with no build
step. It had no hosting — you could only open the file locally. We want it served
on the public web at a clean URL.

The repo was **private**, which the free GitHub Pages tier does not serve, and it
was named `personal-web-page`, which would have published a project site at a
sub-path (`…github.io/personal-web-page/`).

## Decision

Publish via **GitHub Pages as a user site, built by GitHub Actions**:

- **Public repo.** The repo is made public so free Pages can serve it. Only
  résumé-related source is tracked (`index.html`, `update_resume.py`, `README.md`,
  `docs/`, `CLAUDE.md`); the source `.docx` is git-ignored and never committed.
- **User site.** The repo is renamed to `dineshkp-dev.github.io`, so the site
  serves at the root: `https://dineshkp-dev.github.io/`.
- **GitHub Actions deploy**, not "deploy from branch". Pages source is set to
  `workflow`. `.github/workflows/deploy.yml` runs on push to `master` (and manual
  `workflow_dispatch`): it copies **only `index.html`** into a clean `_site/`,
  uploads it with `actions/upload-pages-artifact`, and publishes with
  `actions/deploy-pages`. No Jekyll processing occurs on this path.

## Consequences

- Every merge to `master` redeploys automatically; HTTPS is enforced.
- The published site root contains **only** `index.html`. Source files live in the
  (now public) repo but are not reachable under the site URL.
- This repo is now the account's single user-site repo (`dineshkp-dev.github.io`);
  the git remote changed accordingly. A future project site would need a different
  repo.
- The Actions path means no `.nojekyll` file is needed (Jekyll never runs).

## Alternatives considered

- **Deploy from branch (`master` / root).** Zero YAML, but would serve the entire
  repo root at the site URL (exposing `update_resume.py`, `README.md`, `docs/`
  under the Pages path) and runs Jekyll. Rejected to keep the published surface to
  just the page.
- **Keep it a project site** (`…github.io/personal-web-page/`). No rename needed,
  but a sub-path URL. Rejected in favour of the cleaner root URL.
- **Custom domain.** Best-looking, but requires owning/configuring DNS now; can be
  layered on later via a `CNAME` file without changing this design.
