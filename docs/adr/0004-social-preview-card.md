# ADR 0004 — Ship a social preview card as a deployed image file

Status: Accepted
Date: 2026-08-13

Amends [ADR 0001](0001-standalone-resume-rebuild.md) (self-contained page) and
[ADR 0002](0002-github-pages-deployment.md) (deploy allowlist), and extends the
two-file allowlist that [ADR 0003](0003-downloadable-pdf-and-profile-photo.md)
established.

## Context

The page carried `og:title`, `og:description`, and `og:type`, but no `og:image`
and no `og:url`. Pasting the site link into LinkedIn, Slack, or a message thread
produced a bare text preview with no image — the least persuasive form a résumé
link can take, and the exact moment the page is most likely to be judged.

Fixing it collides with an accepted constraint. ADR 0001 makes `index.html`
self-contained, and every image so far has honoured that by being inlined as a
data URI — the profile photo, the favicon, and the dark-theme backdrop.

**A data URI cannot work here.** `og:image` is consumed by crawlers that never
execute the page: Slack, LinkedIn, Facebook, and X fetch the URL in the tag over
HTTP and expect image bytes back. The value must be an **absolute URL to a real
file**. There is no inlining option to weigh — the requirement is external by
construction.

## Decision

### 1. A committed `og-card.jpg`, deployed alongside the page

`og-card.jpg` (1200×630) is committed to the repo and copied into `_site/` by
`.github/workflows/deploy.yml`. ADR 0002's copy step becomes a **three-file
allowlist**: `index.html`, the PDF, and the card.

The card is referenced absolutely, since relative URLs are invalid in Open Graph:

```
https://dineshkp-dev.github.io/og-card.jpg
```

`og:url`, `og:site_name`, `og:image:{type,width,height,alt}`, and
`twitter:card = summary_large_image` are added alongside it. Twitter falls back
to the `og:` tags for title and description, so those are not duplicated.

### 2. The artwork is generated; the typography is not

The background is generated (OpenArt, GPT Image 2) in the same amber-on-charcoal
register as the backdrop, with the bloom weighted right so the left half stays
dark enough for text.

Everything that carries meaning is **composited deterministically** with Pillow,
not generated: the headshot is read out of the `AVATAR` data URI in `index.html`
so its framing matches the site, and the name, role, and URL are typeset in the
page's own Inter and Source Serif 4.

Image models render text approximately. A résumé card is the wrong place to
accept an approximate spelling of the owner's name.

### 3. JPEG, not PNG

At 1200×630 the card is 130 KB as JPEG q90 with 4:4:4 chroma, against 876 KB as
PNG. Text edges show no visible artefacts at that quality, and the card is never
rendered above its native size.

The build script is not committed. It is a one-shot generator whose inputs
(a generated background, the fonts) are not in the repo; the card is the artefact,
and the procedure is recorded in the README.

## Consequences

- **The page is no longer strictly self-contained for social preview purposes.**
  Opened from disk it still renders completely — the card is only fetched by
  crawlers reading the markup, never by the page itself. The self-contained
  property that ADR 0001 actually protects (open `index.html` anywhere and see
  the résumé) is intact.
- **The deploy allowlist grows to three files.** Each new deployed asset means
  another line in the workflow. This is now a pattern rather than an exception,
  and a fourth asset should prompt asking whether the allowlist should become a
  directory.
- **The card can drift.** It hard-codes the name, role, and tagline, and embeds
  the photo. Changing any of those in the `.docx` updates the page via
  `update_resume.py` but leaves the card stale. `update_resume.py` does not
  regenerate it.
- **Preview caches are sticky.** LinkedIn and Facebook cache aggressively; a
  changed card needs their respective debuggers to force a re-scrape.

## Alternatives considered

- **Fully AI-generated card, text included.** One generation, no compositing
  code. Rejected: image models get letterforms subtly wrong, and the failure mode
  is a misspelled personal name shown to recruiters.
- **Render the card with headless Chrome** from an HTML template, reusing the
  page's CSS. Attractive — the card could not drift from the design — but it adds
  a browser to a pipeline whose only current dependency is Word, and the
  screenshot tooling has already proven fiddly on this repo.
- **Screenshot the actual page** as the card. Zero new artwork, always current,
  but a 1200×630 crop of a dense two-column résumé is illegible as a thumbnail.
- **Skip `og:image` and rely on the text preview.** Free, and honours ADR 0001
  strictly. Rejected: it leaves the link looking unfinished at the moment it
  matters most.
