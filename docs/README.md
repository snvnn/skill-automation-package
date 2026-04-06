# Docs Guide

This `docs/` directory holds project documentation that is intentionally split into current operational references, in-progress working docs, and archived historical records.

## How To Read This Directory

- `docs/operations/`: active canonical runbooks for current maintainers
- `docs/working/`: in-progress design or planning docs that are not current product truth
- `docs/archive/`: preserved historical records, reviews, and legacy notes that are not canonical references for current work

If you are new to this repository, start here:

1. `README.md` at the repository root for product and install behavior
2. `docs/operations/publish-workflow.md` for the current safe publish runbook
3. `docs/docs-information-architecture-analysis-and-archive-plan.md` if you need the reasoning behind the current docs layout

## Current Canonical Docs

- Active operations doc: `docs/operations/publish-workflow.md`
- Active operations doc: `docs/operations/npm-release-workflow.md`
- Root product/install reference: `README.md`

## npm Wrapper Working Docs

The npm wrapper work is not implemented yet, so its documents live under `docs/working/` rather than the active reference set.

Read them in this order:

1. `docs/working/npm-wrapper/npm-wrapper-detailed-design.md`
2. `docs/working/npm-wrapper/npm-wrapper-rollout-plan.md`

`npm-wrapper-detailed-design.md` is the canonical working doc.
`npm-wrapper-rollout-plan.md` is the supporting execution/checklist document.

## Archive Notes

Archive docs are kept for traceability and decision history.
They are useful for context, but they are not the current canonical reference for implementation or operations.

- Review history lives under `docs/archive/reviews/`
- Legacy communication and historical notes live under `docs/archive/legacy/`
