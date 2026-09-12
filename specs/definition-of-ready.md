# Definition of Ready

A feature is ready for implementation only when the required specification records are complete.

## Required records

- [ ] Give the feature a stable ID and a clear title.
- [ ] Write the user story.
- [ ] Write observable acceptance criteria with stable IDs.
- [ ] Record affected files, interfaces, data, risks, and dependencies.
- [ ] Record the design summary, constraints, and rejected alternatives.
- [ ] Record an ADR when the feature changes an architecture decision.
- [ ] Map every acceptance criterion to an automated test or manual check.
- [ ] Record the test command for every automated test.
- [ ] Choose the test fixture locations and data strategy.
- [ ] Record the reason when automated TDD does not apply.

## Gate

Set the feature status to `specified`, `designed`, or `test_designed` only after the matching records are complete.

Do not start implementation while a required record is incomplete.
