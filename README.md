# GovLattice

GovLattice is a Python library for defining governance and quality policies
through a readable fluent API and exporting them as deterministic YAML.

Policies can describe dataset requirements, model-quality thresholds,
conditional segments, lifecycle metadata, external references, and reusable
policy packs. The generated YAML is designed for Git-based review and sharing
across teams.

> GovLattice can verify policies against record-based datasets. Enforcement
> and native Pandas, Polars, Spark, or SQL adapters are not implemented yet.

## Features

- Fluent Python API for policy definitions
- Multiple states in one policy
- Conditional segments within a state
- Column, uniqueness, missing-rate, range, and metric requirements
- Numeric comparison operators: `<`, `<=`, `>`, and `>=`
- Segment range-overlap verification
- Optional purpose, severity, tags, lifecycle stages, timestamps, and links
- Custom YAML-compatible metadata
- Versioned policy packs
- Safe, schema-validated policy reading
- Policy verification with immutable audit results
- Adapter-based datasets and optional actor provenance
- Deterministic YAML with atomic file writes
- JSON Schemas for policy and pack output

## Current Versions

```python
import govlattice

print(govlattice.__version__)              # 0.10.0
print(govlattice.__schema_version__)       # 1.6.0
print(govlattice.__pack_schema_version__)  # 1.2.0
```

## Local Setup

GovLattice does not yet have published-package build configuration. Use the
repository's virtual environment for local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Run commands from the repository root so Python can resolve the local
`govlattice` package.

## Quick Start

```python
from govlattice import (
    ComparisonOperator,
    PolicyDesigner,
    PolicyReference,
    SeverityLevel,
)

policy = (
    PolicyDesigner(
        policy_name="health-data-quality",
        purpose="Ensure health datasets are complete and reliable.",
        severity=SeverityLevel.HIGH,
        tags=("health", "data-quality"),
        lifecycle_stages=("validation",),
        references=(
            PolicyReference(
                title="Health data standard",
                url="https://example.com/health-data-standard",
            ),
        ),
        owner="data-quality-team",
    )
    .state("raw_dataset")
        .require_columns("id", "age", "hba1c")
        .require_unique("id")
    .end()
    .state("validated_dataset")
        .require_missing_rate("hba1c", maximum=0.05)
        .require_column_value(
            "age",
            18,
            operator=ComparisonOperator.GTE,
        )
        .require_metric("recall", 0.8)
    .end()
)

output_path = policy.execute("health_data_quality.yml")
print(output_path)
```

By default, the generated file is written to:

```text
<current-working-directory>/policies/health_data_quality.yml
```

GovLattice creates the `policies` directory when it does not exist.

## Core Concepts

A policy is organized as:

```text
Policy
└── State
    ├── Requirement
    └── Segment
        ├── Condition
        └── Requirement
```

- A **policy** is one governance unit and exports to one YAML file.
- A **state** represents a stage or form of a governed resource, such as
  `raw_dataset`, `validated_dataset`, or `ai_system`.
- A **segment** represents a conditional cohort inside one state.
- A **requirement** defines a rule for an entire state or one segment.

Use `.end()` to return to the parent builder:

- Segment → state
- State → policy

## Requirements

All current requirement methods are available at both state and segment level.

### Required columns

```python
.require_columns("id", "name")
```

### Unique columns

```python
.require_unique("id")
```

### Maximum missing rate

```python
.require_missing_rate("hba1c", maximum=0.05)
```

The maximum must be between `0` and `1`.

### Numeric range

```python
.require_range("age", minimum=18, maximum=100)
```

Range boundaries are inclusive.

### Metric threshold

```python
.require_metric("recall", 0.8)
```

The default operator is `>=`, so this requires `recall >= 0.8`.

For a different comparison:

```python
.require_metric(
    "false_positive_rate",
    0.1,
    operator=ComparisonOperator.LTE,
)
```

Metric values must be between `0` and `1`. The previous keyword form remains
supported:

```python
.require_metric("recall", minimum=0.8)
```

Do not provide both `value` and `minimum`.

### Multiple metrics

```python
.require_metrics(
    ("recall", "precision"),
    (0.8, 0.75),
)
```

`require_metrics()` does not currently support a different operator for each
metric. Use multiple `require_metric()` calls when operators differ.

### Column value comparison

```python
.require_column_value(
    "age",
    18,
    operator=ComparisonOperator.GTE,
)
```

Supported operators:

```python
ComparisonOperator.LT   # <
ComparisonOperator.LTE  # <=
ComparisonOperator.GT   # >
ComparisonOperator.GTE  # >=
```

Raw operator strings are rejected; pass a `ComparisonOperator`.

## Conditional Segments

Use segments when requirements differ between cohorts in the same state:

```python
policy = (
    PolicyDesigner(
        "age-segment-policy",
        purpose="Apply different quality thresholds by age group.",
    )
    .state("validated_dataset")
        .segment("adult")
            .when_between("age", minimum=18, maximum=59)
            .require_missing_rate("hba1c", maximum=0.05)
        .end()
        .segment("senior")
            .when_between("age", minimum=60, maximum=100)
            .require_missing_rate("hba1c", maximum=0.02)
        .end()
        .verify_overlap_range("age")
    .end()
)
```

`.verify_overlap_range("age")` checks only the selected column and current
state. Boundaries are inclusive, so `10-20` and `20-30` overlap.

The verifier does not currently detect gaps or compare ranges across states.

## Policy Metadata

```python
PolicyDesigner(
    policy_name="model-quality",
    purpose="Define quality thresholds for a production model.",
    enabled=True,
    severity=SeverityLevel.CRITICAL,
    tags=("model", "production"),
    lifecycle_stages=("deployment", "operation"),
    created_at="2026-07-01T09:00:00+07:00",
    updated_at="2026-07-27T17:30:00+07:00",
    owner="responsible-ai-team",
)
```

Standard metadata includes:

- `purpose`: Optional non-empty description of the policy's objective.
- `enabled`: Boolean activation metadata.
- `severity`: `INFO`, `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- `tags`: Labels for discovery and grouping.
- `lifecycle_stages`: Data, model, or system lifecycle stages.
- `references`: Optional HTTP or HTTPS references.
- `created_at` and `updated_at`: Optional timezone-aware ISO 8601 timestamps.

Additional keyword arguments become custom policy metadata. Values must be
YAML-compatible: null, strings, booleans, finite numbers, sequences, or
string-keyed objects.

Timestamps are never generated automatically, which keeps output deterministic
and prevents noisy Git diffs.

## Policy Packs

A policy pack groups separate policies under one regulation, standard, or
governance framework:

```python
from govlattice import PolicyDesigner, PolicyPackDesigner, SeverityLevel

data_governance = (
    PolicyDesigner(
        "data-governance",
        purpose="Ensure training data meets governance requirements.",
        severity=SeverityLevel.HIGH,
    )
    .state("training_dataset")
    .require_columns("id", "source", "consent")
    .end()
)

pack = (
    PolicyPackDesigner(
        pack_id="eu-ai-act",
        name="EU AI Act",
        version="1.0.0",
        purpose="Group policies supporting EU AI Act compliance.",
        jurisdiction=("EU",),
        tags=("ai-governance", "regulatory"),
    )
    .add_policy(data_governance)
    .verify_unique_policy_ids()
    .verify_schema_versions()
    .verify_policy_references()
)

manifest_path = pack.execute("eu-ai-act")
```

The output structure is:

```text
policies/
└── eu-ai-act/
    ├── manifest.yml
    └── policies/
        └── data-governance.yml
```

Pack verification runs automatically during `execute()`. Explicit verifier
calls are useful when validation should fail before export starts.

## Reading a Policy

Use `PolicyReader` to safely load and validate a generated policy:

```python
from govlattice import PolicyReader

policy = PolicyReader.read("policies/health_data_quality.yml")

print(policy.name)
print(policy.purpose)
print(policy.schema_version)

for state_id, state in policy.states.items():
    print(state_id, state.requirements)
```

The reader:

- Accepts `.yml` and `.yaml` files.
- Uses the PyYAML safe loader.
- Rejects duplicate YAML keys and unsafe Python YAML tags.
- Rejects files larger than 1 MiB.
- Validates the document against the policy JSON Schema.
- Supports only the current policy schema version.
- Converts severity and comparison operators back to enums.
- Returns frozen, slotted dataclass definitions and recursively read-only
  metadata.

Internally, reading follows four reusable responsibilities:

```text
PolicyYamlLoader
    → PolicyValidator
        → JsonSchemaValidator
    → PolicyDefinitionFactory
```

`JsonSchemaValidator` is reusable for future document types such as
policy-pack manifests and caches compiled validators by schema path.

Reader errors share one base class:

```python
from govlattice import (
    PolicyFileError,
    PolicyReadError,
    PolicySyntaxError,
    PolicyValidationError,
    UnsupportedPolicySchemaError,
)
```

### Reading a policy pack

`PolicyPackReader` validates a manifest and eagerly loads every referenced
policy through `PolicyReader`:

```python
from govlattice import PolicyPackReader

pack = PolicyPackReader.read(
    "policies/eu-ai-act/manifest.yml"
)

print(pack.name, pack.version)

for policy_id, entry in pack.policies.items():
    print(policy_id, entry.severity)
    print(entry.policy.states)
```

The pack reader:

- Validates pack schema version `1.2.0`.
- Validates the manifest with the reusable `JsonSchemaValidator`.
- Rejects missing policy files, duplicate IDs, and duplicate file references.
- Prevents absolute paths, traversal, and symlink escapes.
- Requires referenced files to remain under the pack's `policies/` directory.
- Ensures manifest ID, enabled state, severity, and schema version match each
  loaded policy.
- Returns frozen, slotted `PolicyPackDefinition` and
  `PolicyPackEntryDefinition` objects.

Both readers currently support only their current schema versions. Schema
migration is not implemented yet.

## Verifying a Policy

`GovLatticeEngine.verify()` evaluates a loaded policy without blocking the
calling workflow when requirements fail:

```python
from govlattice import (
    ActorProfile,
    EvaluationContext,
    ExecutionContext,
    GovLatticeEngine,
    PolicyReader,
    RecordsDatasetAdapter,
)

policy = PolicyReader.read("policies/health_policy.yml")

context = EvaluationContext(
    RecordsDatasetAdapter(
        [
            {
                "id": 1,
                "email": "a@example.com",
                "age": 30,
                "hba1c": 5.4,
            },
            {
                "id": 1,
                "email": "b@example.com",
                "age": 65,
                "hba1c": 6.1,
            },
        ]
    ),
    metrics={"recall": 0.9},
    execution=ExecutionContext(
        actor=ActorProfile(
            "user-1842",
            display_name="Logan",
            team="data-quality",
        ),
        environment="staging",
        run_id="run-001",
    ),
)

result = GovLatticeEngine().verify(
    policy,
    state="validated_dataset",
    context=context,
)

print(result.status)
print(result.passed_count)
print(result.failed_count)
print(result.error_count)
```

Verification behavior:

- Requires an explicit policy state.
- Evaluates state requirements against the full dataset.
- Filters each segment with its inclusive `between` condition.
- Evaluates segment requirements against the filtered records.
- Treats `require_unique("id", "email")` as composite uniqueness.
- Returns `FAILED` as a result and does not raise for non-compliance.
- Returns `ERROR` findings for missing metrics, missing required evaluation
  columns, unsupported evaluators, and non-comparable values.
- Treats an empty state dataset as `ERROR`.
- Treats an empty segment as `SKIPPED`.
- Treats a disabled policy as `SKIPPED`.
- Accepts an optional actor profile; a missing actor does not skip policy
  evaluation.
- Records start time, completion time, duration, environment, run ID, source,
  and actor snapshot.

Current statuses are:

```python
EvaluationStatus.PASSED
EvaluationStatus.FAILED
EvaluationStatus.SKIPPED
EvaluationStatus.ERROR
```

The initial adapter is `RecordsDatasetAdapter`, which accepts a list or tuple
of mapping records. `DatasetAdapter` is a runtime-checkable protocol for
future Pandas, Polars, Spark, or SQL adapters.

Built-in evaluators support all current requirement types. Custom evaluators
can be registered through `GovLatticeEngine.register_evaluator()`.

```python
from govlattice import RequirementEvaluation


class RowCountEvaluator:
    requirement_type = "require_row_count"

    def evaluate(self, requirement, context):
        minimum = requirement.parameters["minimum"]
        actual = context.dataset.row_count
        result = (
            RequirementEvaluation.passed
            if actual >= minimum
            else RequirementEvaluation.failed
        )
        return result(
            expected=requirement.parameters,
            observed={"row_count": actual},
            message="row count requirement evaluated",
        )


engine = GovLatticeEngine().register_evaluator(RowCountEvaluator())
```

Evaluators receive a stable context containing the scoped dataset, runtime
metrics, and execution information. Duplicate requirement types are rejected
unless registration explicitly uses `replace=True`. The former
`register_evaluator(requirement_type, evaluator)` API remains supported.

`enforce()` is intentionally not implemented yet. The current `verify()`
semantics should be reviewed before enforcement behavior is added.

## YAML Output

Example policy output:

```yaml
schema_version: "1.6.0"
policy:
  name: "model-quality"
  purpose: "Define model quality thresholds."
  enabled: true
  severity: "high"
  tags:
    - "model"
  lifecycle_stages:
    - "validation"
  references: []
  states:
    evaluation:
      requirements:
        - type: "require_metric"
          metric: "recall"
          operator: ">="
          value: 0.8
```

Output behavior:

- Supports `.yml` and `.yaml`.
- Rejects directory traversal in filenames.
- Creates output directories automatically.
- Writes files atomically with permissions `0644`.
- Omits optional `purpose` and timestamps when they are not provided.
- Uses JSON-compatible YAML 1.2 scalars without an external YAML dependency.

## Schemas

The serialized contracts are defined by JSON Schema Draft 2020-12:

```text
schemas/govlattice-policy.schema.json
schemas/govlattice-policy-pack.schema.json
```

Every policy YAML contains `schema_version`. Every pack manifest contains
`pack_schema_version`, and each manifest policy entry records its policy schema
version.

## Development

Run all tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run the examples:

```bash
.venv/bin/python dev/dev_policy_desinger.py
.venv/bin/python dev/dev_pack_eu_ai_act.py
.venv/bin/python dev/dev_policy_reader.py
.venv/bin/python dev/dev_policy_pack_reader.py
.venv/bin/python dev/dev_engine_verify.py
```

Generated files are written under `policies/`, which is ignored by Git.

For architectural details, validation rules, design decisions, and current
limitations, see [context/project.md](context/project.md).
