---
inclusion: always
---

# Project Context

Treat the files in `specs/` as the project source of truth.

Read `specs/development-workflow.md` before you start a feature.

## Canonical project context

#[[file:specs/system-architecture.yaml]]
#[[file:specs/context-map.yaml]]
#[[file:specs/active-feature.yaml]]
#[[file:specs/state.yaml]]
#[[file:specs/verification-protocol.md]]
#[[file:specs/development-workflow.md]]

Run `specs/validate-context.sh` before you integrate or complete a change.

Run `specs/validate-context.sh --strict` before you archive a complete feature.

Run `specs/archive-feature.sh` before you start another feature.
