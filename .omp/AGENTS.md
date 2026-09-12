# OMP Project Steering

Treat the files in `specs/` as the project source of truth.

Read `specs/development-workflow.md` before you start a feature.

## Canonical project context

@../specs/system-architecture.yaml
@../specs/context-map.yaml
@../specs/active-feature.yaml
@../specs/state.yaml
@../specs/verification-protocol.md
@../specs/development-workflow.md

## OMP-specific configuration

@tool-routing.yaml
@lsp-guardrails.yaml

Run `specs/validate-context.sh --strict` before you archive a complete feature.

Run `specs/archive-feature.sh` before you start another feature.
Run `specs/validate-context.sh` before you integrate or complete a change.
