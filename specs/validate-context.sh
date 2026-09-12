#!/usr/bin/env bash
set -Eeuo pipefail

SPEC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "$SPEC_DIR/.." && pwd -P)"

exec ruby "$SPEC_DIR/validate-context.rb" "$@" "$SPEC_DIR" "$PROJECT_DIR"
