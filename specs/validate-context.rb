require "yaml"
require "pathname"

strict = ARGV.delete("--strict")
spec_dir = Pathname.new(ARGV.fetch(0))
project_dir = Pathname.new(ARGV.fetch(1))
root_dir = if spec_dir.join("AGENTS.md").file?
  spec_dir
elsif project_dir.join("AGENTS.md").file?
  project_dir
else
  project_dir
end
root_required_files = %w[
  AGENTS.md
  CHANGELOG.md
  CONVENTIONS.md
  CONTRIBUTING.md
  .editorconfig
  .gitattributes
  .gitignore
  VERSION
]
root_required_files.each do |name|
  path = root_dir.join(name)
  abort "Missing required project file: #{path}" unless path.file?
end
version = root_dir.join("VERSION").read.strip
semver_pattern = /\A(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\z/
abort "VERSION must contain a semantic version: #{version.inspect}" unless semver_pattern.match?(version)
changelog = root_dir.join("CHANGELOG.md").read
abort "CHANGELOG.md must identify Keep a Changelog" unless changelog.include?("Keep a Changelog")
abort "CHANGELOG.md must contain an Unreleased section" unless changelog.match?(/^## \[Unreleased\]$/)
changelog.scan(/^## \[([^\]]+)\](?: - \d{4}-\d{2}-\d{2})?$/).each do |heading|
  next if heading.first == "Unreleased"
  abort "CHANGELOG.md release heading must contain a semantic version: #{heading.first.inspect}" unless semver_pattern.match?(heading.first)
end
allowed_changelog_categories = %w[Added Changed Deprecated Removed Fixed Security]
changelog.scan(/^### (.+)$/).each do |heading|
  abort "Unsupported CHANGELOG.md category: #{heading.first.inspect}" unless allowed_changelog_categories.include?(heading.first)
end
required_files = %w[
  active-feature.yaml
  archive-feature.sh
  context-map.yaml
  definition-of-done.md
  definition-of-ready.md
  decisions/000-template.md
  development-workflow.md
  run-feature-tests.sh
  state.yaml
  system-architecture.yaml
  test-strategy.md
  validate-context.rb
  validate-context.sh
  verification-protocol.md
]
required_files.each do |name|
  path = spec_dir.join(name)
  abort "Missing required context file: #{path}" unless path.file?
end

def load_yaml(path)
  value = YAML.safe_load(File.read(path), aliases: false)
  abort "YAML document must be a mapping: #{path}" unless value.is_a?(Hash)
  value
rescue Psych::Exception => error
  abort "Invalid YAML: #{path}: #{error.message.lines.first.strip}"
end

def require_text(value, message)
  abort message if value.nil? || value.to_s.strip.empty?
end

def require_array(value, message)
  abort message unless value.is_a?(Array)
end

def placeholders(value, path = [])
  found = []
  case value
  when Hash
    value.each { |key, child| found.concat(placeholders(child, path + [key])) }
  when Array
    value.each_with_index { |child, index| found.concat(placeholders(child, path + [index])) }
  when String
    if value == "UNASSIGNED" || value == "unassigned" || value.start_with?("Replace with") || value.match?(/\A<[^>]+>\z/)
      found << [path.join("."), value]
    end
  end
  found
end

def check_reference(path, target)
  abort "Missing referenced file: #{path} -> #{target}" unless target.file?
end

archive_files = spec_dir.join("features").glob("*.yaml")
yaml_files = spec_dir.glob("*.yaml") + archive_files + project_dir.join(".omp").glob("*.yaml")
yaml_documents = yaml_files.to_h { |path| [path, load_yaml(path)] }

if strict
  yaml_documents.each do |path, document|
    placeholders(document).each do |location, value|
      abort "Unresolved placeholder in strict mode at #{path}:#{location}: #{value.inspect}"
    end
  end
end

state = yaml_documents.fetch(spec_dir.join("state.yaml"))
feature = yaml_documents.fetch(spec_dir.join("active-feature.yaml"))

archive_files.each do |path|
  archive = yaml_documents.fetch(path)
  abort "Archived feature must use schema version 1.0: #{path}" unless archive["schema_version"] == "1.0"
  abort "Archived feature requires feature_id: #{path}" unless archive["feature_id"].is_a?(String) && !archive["feature_id"].empty?
  abort "Archived feature must have status=complete: #{path}" unless archive["status"] == "complete"
end

abort "Unsupported active-feature schema version: #{feature["schema_version"].inspect}" unless feature["schema_version"] == "1.0"
abort "Unsupported state schema version: #{state["schema_version"].inspect}" unless state["schema_version"] == "1.0"

meta = state["meta"]
abort "state.meta must be a mapping" unless meta.is_a?(Hash)
state_feature_id = meta["active_feature_id"]
abort "state.meta.active_feature_id must be text or null" unless state_feature_id.nil? || state_feature_id.is_a?(String)
feature_id = feature["feature_id"]
if state_feature_id != feature_id
  abort "Active feature mismatch: state.yaml=#{state_feature_id.inspect}, active-feature.yaml=#{feature_id.inspect}"
end

milestone = state["milestone"]
abort "state.milestone must be a mapping" unless milestone.is_a?(Hash)
phase_ids = %w[discovery specification design test_design implementation verification complete]
phase_names = {
  "discovery" => "Discovery",
  "specification" => "Specification",
  "design" => "Design",
  "test_design" => "Test design",
  "implementation" => "Implementation",
  "verification" => "Verification",
  "complete" => "Complete"
}
phase_id = milestone["phase_id"]
abort "Unknown milestone phase: #{phase_id.inspect}" unless phase_ids.include?(phase_id)
abort "Milestone phase_name does not match phase_id" unless milestone["phase_name"] == phase_names[phase_id]
completion = milestone["completion_percentage"]
unless completion.is_a?(Numeric) && completion.between?(0, 100)
  abort "Milestone completion_percentage must be between 0 and 100"
end

status_board = state["status_board"]
abort "state.status_board must be a mapping" unless status_board.is_a?(Hash)
abort "status_board.blocked must be true or false" unless [true, false].include?(status_board["blocked"])
require_array(status_board["in_flight"], "status_board.in_flight must be an array")
require_array(status_board["completed"], "status_board.completed must be an array")
%w[in_flight completed].each do |bucket|
  status_board[bucket].each_with_index do |entry, index|
    abort "status_board.#{bucket} entry #{index} must be a mapping" unless entry.is_a?(Hash)
    require_text(entry["id"], "status_board.#{bucket} entry #{index} requires id")
    require_text(entry["title"], "status_board.#{bucket} entry #{index} requires title")
  end
end
if status_board["blocked"]
  require_text(status_board["block_reason"], "Blocked state requires status_board.block_reason")
end

system_health = state["system_health"]
abort "state.system_health must be a mapping" unless system_health.is_a?(Hash)
health_values = %w[not_run pending passed failed skipped]
%w[formatting linting build type_check unit_tests integration_tests end_to_end_tests].each do |check|
  abort "Unknown system health value for #{check}: #{system_health[check].inspect}" unless health_values.include?(system_health[check])
end

task_checklist = state["task_checklist"]
require_array(task_checklist, "state.task_checklist must be an array")
task_statuses = %w[pending in_progress blocked complete]
task_checklist.each_with_index do |task, index|
  abort "Task checklist entry #{index} must be a mapping" unless task.is_a?(Hash)
  require_text(task["id"], "Task checklist entry #{index} requires id")
  require_text(task["title"], "Task checklist entry #{index} requires title")
  abort "Unknown task status for #{task["id"]}: #{task["status"].inspect}" unless task_statuses.include?(task["status"])
end

feature_statuses = %w[unassigned draft specified designed test_designed implementing verifying blocked complete]
feature_status = feature["status"]
abort "Unknown feature status: #{feature_status.inspect}" unless feature_statuses.include?(feature_status)

identity_statuses = %w[specified designed test_designed implementing verifying blocked complete]
if identity_statuses.include?(feature_status)
  require_text(feature_id, "Active feature requires feature_id")
  require_text(feature["title"], "Active feature requires title")
end

phase_by_status = {
  "specified" => "specification",
  "designed" => "design",
  "test_designed" => "test_design",
  "implementing" => "implementation",
  "verifying" => "verification",
  "complete" => "complete"
}
expected_phase = phase_by_status[feature_status]
if expected_phase && phase_id != expected_phase
  abort "Feature status #{feature_status.inspect} requires milestone phase #{expected_phase.inspect}, got #{phase_id.inspect}"
end

if feature_status == "blocked"
  abort "Blocked feature requires status_board.blocked=true" unless status_board["blocked"] == true
  require_text(status_board["block_reason"], "Blocked feature requires status_board.block_reason")
end

if %w[specified designed test_designed implementing verifying complete].include?(feature_status)
  criteria = feature["acceptance_criteria"]
  require_array(criteria, "acceptance_criteria must be an array")
  abort "Active feature requires at least one acceptance criterion" if criteria.empty?

  criterion_ids = {}
  criteria.each_with_index do |criterion, index|
    abort "Acceptance criterion #{index} must be a mapping" unless criterion.is_a?(Hash)
    id = criterion["id"]
    require_text(id, "Acceptance criterion #{index} requires id")
    abort "Duplicate acceptance criterion id: #{id}" if criterion_ids.key?(id)
    criterion_ids[id] = true
    require_text(criterion["statement"], "Acceptance criterion #{id} requires statement")
  end

  if %w[designed test_designed implementing verifying complete].include?(feature_status)
    design = feature["design"]
    abort "Active feature requires a design mapping" unless design.is_a?(Hash)
    require_text(design["summary"], "Active feature requires design.summary")
    impact = feature["impact"]
    abort "Active feature requires an impact mapping" unless impact.is_a?(Hash)
    %w[affected_modules affected_data affected_external_interfaces compatibility_risks dependencies risks].each do |field|
      require_array(impact[field], "Active feature impact.#{field} must be an array")
    end
    abort "Active feature impact.migration_required must be true or false" unless [true, false].include?(impact["migration_required"])
    decision_records = feature["decision_records"] || []
    require_array(decision_records, "Active feature decision_records must be an array")
    decision_records.each do |path|
      require_text(path, "Active feature decision record paths must contain text")
      relative_path = Pathname.new(path)
      abort "Decision record reference must be relative: #{path}" if relative_path.absolute?
      abort "Missing decision record: #{path}" unless root_dir.join(relative_path).file?
    end
  end

  if %w[test_designed implementing verifying complete].include?(feature_status)
    test_plan = feature["test_plan"]
    abort "Active feature requires a test_plan mapping" unless test_plan.is_a?(Hash)
    mode = test_plan["mode"]
    abort "test_plan.mode must be automated, manual, or mixed" unless %w[automated manual mixed].include?(mode)
    require_text(test_plan["reason"], "Manual test plans require test_plan.reason") if mode == "manual"

    tests = test_plan["tests"] || []
    manual_checks = test_plan["manual_checks"] || []
    fixture_paths = test_plan["fixture_paths"] || []
    require_array(tests, "test_plan.tests must be an array")
    require_array(manual_checks, "test_plan.manual_checks must be an array")
    require_array(fixture_paths, "test_plan.fixture_paths must be an array")
    fixture_paths.each do |path|
      require_text(path, "Test fixture paths must contain text")
      relative_path = Pathname.new(path)
      abort "Test fixture reference must be relative: #{path}" if relative_path.absolute?
      abort "Missing referenced test fixture: #{path}" unless root_dir.join(relative_path).exist?
    end

    test_ids = {}
    tests.each_with_index do |test, index|
      abort "Test #{index} must be a mapping" unless test.is_a?(Hash)
      id = test["id"]
      require_text(id, "Test #{index} requires id")
      abort "Duplicate test id: #{id}" if test_ids.key?(id)
      test_ids[id] = true
      result = test["result"] || "not_run"
      abort "Unknown result for test #{id}: #{result.inspect}" unless %w[not_run red passed failed skipped].include?(result)
      if test["file"]
        abort "Test file reference must be relative: #{test["file"]}" if Pathname.new(test["file"]).absolute?
        abort "Missing referenced test file: #{test["file"]}" unless root_dir.join(test["file"]).file?
      end
    end
    if %w[test_designed implementing verifying complete].include?(feature_status) && %w[automated mixed].include?(mode)
      abort "Automated test plans require at least one test" if tests.empty?
      tests.each do |test|
        require_text(test["file"], "Automated test #{test["id"]} requires file")
        require_text(test["name"], "Automated test #{test["id"]} requires name")
        require_text(test["command"], "Automated test #{test["id"]} requires command")
      end
    end

    manual_ids = {}
    manual_checks.each_with_index do |check, index|
      abort "Manual check #{index} must be a mapping" unless check.is_a?(Hash)
      id = check["id"]
      require_text(id, "Manual check #{index} requires id")
      require_text(check["description"], "Manual check #{id} requires description")
      abort "Duplicate manual check id: #{id}" if manual_ids.key?(id)
      manual_ids[id] = true
      result = check["result"] || "not_run"
      abort "Unknown result for manual check #{id}: #{result.inspect}" unless %w[not_run passed failed skipped].include?(result)
    end

    referenced_tests = []
    referenced_manual_checks = []
    criteria.each do |criterion|
      verification = criterion["verification"]
      abort "Acceptance criterion #{criterion["id"]} requires verification mapping" unless verification.is_a?(Hash)
      criterion_tests = verification["tests"] || []
      criterion_manual_checks = verification["manual_checks"] || []
      require_array(criterion_tests, "Acceptance criterion #{criterion["id"]} tests must be an array")
      require_array(criterion_manual_checks, "Acceptance criterion #{criterion["id"]} manual_checks must be an array")
      criterion_tests.each do |id|
        abort "Acceptance criterion #{criterion["id"]} references unknown test: #{id}" unless test_ids.key?(id)
        referenced_tests << id
      end
      criterion_manual_checks.each do |id|
        abort "Acceptance criterion #{criterion["id"]} references unknown manual check: #{id}" unless manual_ids.key?(id)
        referenced_manual_checks << id
      end
      if mode == "automated" && criterion_tests.empty?
        abort "Acceptance criterion #{criterion["id"]} requires a test in automated mode"
      elsif mode == "manual" && criterion_manual_checks.empty?
        abort "Acceptance criterion #{criterion["id"]} requires a manual check in manual mode"
      elsif mode == "mixed" && criterion_tests.empty? && criterion_manual_checks.empty?
        abort "Acceptance criterion #{criterion["id"]} requires a test or manual check"
      end
    end
    if %w[test_designed implementing verifying complete].include?(feature_status)
      tests.each do |test|
        abort "Test #{test["id"]} is not mapped to an acceptance criterion" unless referenced_tests.include?(test["id"])
      end
      manual_checks.each do |check|
        abort "Manual check #{check["id"]} is not mapped to an acceptance criterion" unless referenced_manual_checks.include?(check["id"])
      end
    end

    if %w[implementing verifying complete].include?(feature_status) && %w[automated mixed].include?(mode)
      tests.each do |test|
        require_text(test["red_evidence"], "Automated test #{test["id"]} requires red_evidence")
      end
    end
    if feature_status == "complete"
      verification = feature["verification"]
      abort "Complete feature requires a verification mapping" unless verification.is_a?(Hash)
      abort "Complete feature requires verification.status=passed" unless verification["status"] == "passed"
      evidence = verification["evidence"]
      require_array(evidence, "Complete feature requires verification.evidence")
      abort "Complete feature requires verification evidence" if evidence.empty?
      tests.each do |test|
        abort "Complete feature has an unpassed test: #{test["id"]}" unless test["result"] == "passed"
      end
      manual_checks.each do |check|
        next unless referenced_manual_checks.include?(check["id"])
        abort "Complete feature has an unpassed manual check: #{check["id"]}" unless check["result"] == "passed"
      end
    end
  end

  placeholders(feature).each do |path, value|
    abort "Unresolved placeholder in active-feature.yaml at #{path}: #{value.inspect}"
  end
end

omp_agents = project_dir.join(".omp", "AGENTS.md")
if omp_agents.file?
  omp_agents.read.scan(/(?:^|[ \t])@([^\s`]+)/).each do |match|
    token = match.first.sub(/[.,;:!?]+\z/, "")
    next if token.start_with?("/", "~")
    check_reference(omp_agents, omp_agents.dirname.join(token))
  end
end

kiro_context = project_dir.join(".kiro", "steering", "project-context.md")
if kiro_context.file?
  kiro_context.read.scan(/#\[\[file:([^\]]+)\]\]/).each do |match|
    check_reference(kiro_context, project_dir.join(match.first))
  end
end

if strict && feature_status != "complete"
  abort "Strict validation requires feature status=complete"
end

puts "Context validation passed: #{yaml_files.length} YAML files checked#{strict ? " in strict mode" : ""}."
