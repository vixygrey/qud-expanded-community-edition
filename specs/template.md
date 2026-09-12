# Specification: Feature specification

## Status

- Status: Draft
- Issue: Record the repository issue number or URL.

## Scope

Describe the feature or change that this specification covers.

## Observable Behavior

Describe what a player, contributor, tool, or system can observe.

## Prerequisites

List the conditions that MUST exist before the behavior starts.

## Safety Rules

List data protection, security, compatibility, save-identifier, merge, and destructive-action rules.

## Failure Behavior

Describe errors, rejected actions, fallback behavior, and recovery steps.

## Related Files

- `docs/CHARTER.md`: project compatibility and safety rules
- `docs/STYLEGUIDE.md`: shipped-content conventions
- `specs/active-feature.yaml`: feature records and verification mapping
- `mod/`: shipped Qud content
- `tools/`: validation and test tooling

## Verification

List the applicable commands or scenarios that prove the specification.

- `python3 tools/validate_mod.py --all`
- `python3 tools/check_docs.py`
- `python3 -m unittest discover -s tools -v`
- `npx prettier --check "mod/**/*.xml" "mod/**/*.rpm"`
