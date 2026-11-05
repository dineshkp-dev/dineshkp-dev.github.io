# ADR 0005 — Track the source `.docx` in the public repo

Status: Accepted
Date: 2026-11-04

Reverses the `.docx` exclusion in [ADR 0002](0002-github-pages-deployment.md) and
[ADR 0003](0003-downloadable-pdf-and-profile-photo.md). Their deployment and PDF
decisions otherwise stand.

## Context

`index.html` and `Dinesh-Kumar-Pulikesi-Resume.pdf` are both generated from
`Pulikesi_Dinesh_Kumar.docx`, yet the source was the one file with no version
history. Only its outputs were committed, so an earlier revision of the résumé
could not be recovered or regenerated, and the file lived on a single machine.

ADR 0002 and ADR 0003 kept it git-ignored because the repo is public: committing
it would publish Word metadata and an editable copy. Tracking was tried and
reverted on 2026-08-22.

## Decision

Commit `Pulikesi_Dinesh_Kumar.docx` and update it alongside its generated outputs
in every résumé change. Remove it from `.gitignore`. Word's `~$*.docx` lock files
stay ignored.

The docx remains **unpublished on the site**: the deploy step is an explicit
allowlist, and it is not on it.

## Consequences

- Résumé history is recoverable, and the source is no longer tied to one machine.
- Anyone can download the editable file from the GitHub repo, though not from the
  site URL.
- Word metadata becomes public. At adoption that is the author name, created and
  modified dates, revision count, and total editing time. The file had no
  comments, tracked changes, or hidden text; a later revision could add them, so
  check before committing.
- **Every committed revision stays in public history.** Removing something from
  the résumé, such as a phone number, removes it from the page and PDF but not
  from earlier commits. Purging it would take a history rewrite, and copies may
  already exist elsewhere.
- Each revision adds a ~30 KB binary to the repo, and diffs show no text changes.

## Alternatives considered

- **Keep it git-ignored.** No new exposure, but no history for the source file.
- **Store it in a private repo or backup.** Gives history without publishing it,
  at the cost of a second place to keep in sync with the generated outputs.
- **Commit a metadata-stripped copy.** Removes little that matters, because the
  history risk comes from the résumé's content rather than its metadata, and it
  adds a step to every update.
