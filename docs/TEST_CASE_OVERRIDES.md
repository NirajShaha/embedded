# Per-project test case overrides

Users can edit a test case's details from the dashboard. The master
`test_cases` catalogue is never written — edits are stored per project and
merged over the master rows when reading and when generating the Test Plan PDF.

## Data model

- `project_test_case_overrides` — one row per `(project_id, test_case_id)`.
- `project_test_case_override_tools`, `project_test_case_override_references` —
  replacement tool/reference link sets for the override.

Merge rule: a non-`NULL` override column replaces the master value. `NULL`
means "not overridden"; an empty string explicitly clears the field for that
project. A row that ends up overriding nothing is deleted, so `is_overridden`
never reports a no-op edit.

Editable: `action_test_case`, `source_scope_status`, `description`,
`attack_path`, `test_steps`, `expected_output`, `attack_feasibility`,
`cia_impact`, `safety_impact`, `automation_possible`, plus tools and references.
Classifications (category, objective, test type, severity, protocol, attack
vector, threat, asset) are read-only and still drive filtering.

## API

- `GET /api/test-cases?project_id=N` and `GET /api/test-cases/{id}?project_id=N`
  return master values with the project's overrides merged, plus
  `is_overridden: bool`. Omitting `project_id` returns master data unchanged.
- `GET /api/test-cases/tools` and `/api/test-cases/references` list the master
  link options for the edit pickers.
- `PUT /api/projects/{id}/test-cases/{caseId}` with a `TestCaseOverrideUpdate`
  body upserts the override (scalar fields verbatim; `tools`/`references` are
  full replacement sets, `[]` removes all, `null`/absent leaves master links).
  Unknown ids return 400; unknown project or test case return 404.
- `DELETE /api/projects/{id}/test-cases/{caseId}` removes the override so the
  master values apply again (children cascade).
- `GET /api/test-cases/export/pdf?project_id=N` merges overrides before building
  the document, so section 4 "Test scope" shows each project's edited text.

## UI

The test case dialog has a read/edit toggle. Edit mode reuses the existing
`EcuFormDialog` form pattern (local `FormState`, `useMutation`, `DialogFooter`
Cancel/Save). The dashboard shows an "Edited" badge on rows with overrides and
derives the open dialog case from the query data so saves reflect immediately.

## Schema changes

`prisma/schema.prisma` and `app/schema/schema.sql` define the three tables.
There is no migration tooling — apply the DDL to `embedded_db` and run
`prisma generate` after editing the schema.
