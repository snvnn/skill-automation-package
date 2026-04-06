# npm Wrapper Phase 6 Roadmap

This document captures post-Phase-5 ideas that are intentionally deferred.

## TODO List

### 1. Partial update flow

- What:
  - Update only shipped package files that changed instead of always doing a full reinstall.
- Why needed:
  - Could reduce repeated overwrite noise and make large target repos cheaper to refresh.
- Why not now:
  - The current reinstall model is simpler, easier to reason about, and already covered by tests.
- Difficulty:
  - High

### 2. Dry-run diff preview

- What:
  - Show a more explicit preview of which managed files or package files would change during install/update.
- Why needed:
  - Operators would get a clearer view than the current summary-only dry-run output.
- Why not now:
  - It adds comparison logic and output design that go beyond the current minimal wrapper scope.
- Difficulty:
  - Medium

### 3. Selective overwrite controls

- What:
  - Allow tighter control over which shipped paths are refreshed during reinstall.
- Why needed:
  - Some downstream repos may want stricter control over managed docs versus packaged assets.
- Why not now:
  - It would expand the public install contract and complicate a workflow that is currently intentionally simple.
- Difficulty:
  - High

### 4. Stale packaged-file cleanup

- What:
  - Detect or remove previously shipped files that are no longer part of the package.
- Why needed:
  - Reinstall currently preserves orphaned old files when the package shrinks.
- Why not now:
  - Cleanup behavior can become destructive if ownership rules are not explicit.
- Difficulty:
  - Medium

### 5. Metadata validation hardening

- What:
  - Validate install metadata more strictly and surface clearer recovery paths for malformed or partial metadata.
- Why needed:
  - The wrapper now detects malformed metadata, but recovery is still conservative and message-driven.
- Why not now:
  - The current fallback behavior is safe enough for release, and deeper validation would likely introduce new policy decisions.
- Difficulty:
  - Low
