#!/usr/bin/env bash
set -Eeuo pipefail

SPEC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ -f "$SPEC_DIR/AGENTS.md" ]]; then
    ROOT_DIR="$SPEC_DIR"
else
    ROOT_DIR="$(cd -- "$SPEC_DIR/.." && pwd -P)"
fi
cd "$ROOT_DIR"
FEATURE_FILE="$SPEC_DIR/active-feature.yaml"
PHASE="green"

case "${1:-}" in
    "")
        ;;
    --red)
        PHASE="red"
        shift
        ;;
    --green)
        PHASE="green"
        shift
        ;;
    *)
        printf 'Usage: run-feature-tests.sh [--red|--green]\n' >&2
        exit 2
        ;;
esac

(($# == 0)) || {
    printf 'Error: unexpected argument: %s\n' "$1" >&2
    exit 2
}

ruby -ryaml -rfileutils -ropen3 -rpathname - "$FEATURE_FILE" "$PHASE" "$ROOT_DIR" <<'RUBY'
require "yaml"
require "fileutils"
require "open3"
require "pathname"
require "time"

feature_path = Pathname.new(ARGV.fetch(0)).expand_path
phase = ARGV.fetch(1)
root_dir = Pathname.new(ARGV.fetch(2)).expand_path
abort "Feature file is a symlink: #{feature_path}" if feature_path.symlink?

feature = YAML.safe_load(File.read(feature_path), aliases: false)
test_plan = feature.fetch("test_plan")
tests = test_plan.fetch("tests", [])
abort "No automated tests are recorded in active-feature.yaml" if tests.empty?

run_dir = Pathname.new(feature_path.dirname).join(".test-results", "#{Time.now.utc.strftime("%Y%m%dT%H%M%SZ")}-#{$$}")
FileUtils.mkdir_p(run_dir)
results = []
failures = 0

tests.each_with_index do |test, index|
  id = test.fetch("id")
  command = test.fetch("command")
  safe_id = id.gsub(/[^A-Za-z0-9._-]/, "_")
  output_path = run_dir.join(format("%03d-%s.log", index + 1, safe_id))
  puts "Running #{id}: #{command}"
  stdout, stderr, status = Open3.capture3("bash", "-lc", command, chdir: root_dir.to_s)
  output = stdout + stderr
  File.write(output_path, output)
  exit_status = status.exitstatus || 1
  passed = status.success?
  if phase == "red"
    if passed
      warn "Expected #{id} to fail during the red phase, but it exited with #{exit_status}"
      test["result"] = "passed"
    else
      puts "Expected failure recorded for #{id} with exit status #{exit_status}"
      test["result"] = "red"
      test["red_evidence"] = root_dir.join(output_path).relative_path_from(root_dir).to_s
      failures += 1
    end
  elsif passed
    puts "Passed #{id}"
    test["result"] = "passed"
  else
    warn "Test #{id} failed with exit status #{exit_status}"
    test["result"] = "failed"
    failures += 1
  end
  results << {
    "id" => id,
    "result" => test["result"],
    "exit_status" => exit_status,
    "output" => root_dir.join(output_path).relative_path_from(root_dir).to_s
  }
end

summary_path = run_dir.join("summary.yaml")
File.write(summary_path, YAML.dump("phase" => phase, "tests" => results))
temporary_path = feature_path.sub_ext(".yaml.tmp.#{$$}")
File.write(temporary_path, YAML.dump(feature))
File.rename(temporary_path, feature_path)
puts "Test results: #{root_dir.join(summary_path).relative_path_from(root_dir)}"

if phase == "red"
  abort "The red phase requires at least one failing automated test" if failures.zero?
elsif failures.positive?
  abort "#{failures} automated test(s) failed"
end
RUBY
