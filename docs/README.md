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

## npm Wrapper Docs

The npm wrapper is implemented and is part of the current product surface.
Use the root `README.md` and `docs/operations/npm-release-workflow.md` as the current canonical references.

Historical planning material remains under `docs/working/npm-wrapper/` for decision traceability.
Read it in this order when you need background context:

1. `docs/working/npm-wrapper/npm-wrapper-detailed-design.md`
2. `docs/working/npm-wrapper/npm-wrapper-rollout-plan.md`

Those files are not the source of truth for current commands or release operations.

## Archive Notes

Archive docs are kept for traceability and decision history.
They are useful for context, but they are not the current canonical reference for implementation or operations.

- Review history lives under `docs/archive/reviews/`
- Legacy communication and historical notes live under `docs/archive/legacy/`
