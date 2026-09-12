#!/usr/bin/env bash
set -Eeuo pipefail

SPEC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ARCHIVE_DIR="$SPEC_DIR/features"

"$SPEC_DIR/validate-context.sh" --strict

feature_id="$(ruby -ryaml -e 'data = YAML.safe_load(File.read(ARGV.fetch(0)), aliases: false); puts data.fetch("feature_id")' "$SPEC_DIR/active-feature.yaml")"
if [[ ! "$feature_id" =~ ^[A-Za-z0-9._-]+$ ]]; then
    printf 'Error: feature_id contains unsupported archive characters: %s\n' "$feature_id" >&2
    exit 1
fi

if [[ -L "$ARCHIVE_DIR" ]]; then
    printf 'Error: archive directory is a symlink: %s\n' "$ARCHIVE_DIR" >&2
    exit 1
fi
mkdir -p "$ARCHIVE_DIR"
archive_path="$ARCHIVE_DIR/$feature_id.yaml"
if [[ -e "$archive_path" || -L "$archive_path" ]]; then
    printf 'Error: archive destination already exists: %s\n' "$archive_path" >&2
    exit 1
fi

cp -p "$SPEC_DIR/active-feature.yaml" "$archive_path"
printf 'Archived completed feature to %s\n' "$archive_path"
