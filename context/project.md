# GovLattice Project Context

This document is the primary reference for understanding GovLattice without
reading the entire source tree first. Update it whenever the public API,
schemas, validation rules, output structure, or architectural decisions
change.

## 1. Project Overview

GovLattice is a Python package for defining governance and quality policies
through a fluent API and exporting them as readable YAML. The generated files
are suitable for Git-based review, collaboration, and submission to other
teams.

The current system can:

- Create policies in Python.
- Divide a policy into multiple states.
- Attach requirements to an entire state.
- Divide a state into conditional segments.
- Attach requirements to individual segments.
- Detect overlapping segment ranges within a state.
- Group multiple policies into a versioned policy pack.
- Export policies and packs as deterministic YAML.
- Safely read and validate exported policy YAML.
- Validate inputs before writing files.

GovLattice currently **defines and exports policies**. It does not yet include
a runtime engine that evaluates a dataset or model against an exported policy.

## 2. Current Versions

The package root exposes three version constants:

```python
import govlattice

govlattice.__version__              # "0.9.0"
govlattice.__schema_version__       # "1.6.0"
govlattice.__pack_schema_version__  # "1.2.0"
```

Their responsibilities are:

- `__version__`: Python package version.
- `__schema_version__`: Policy YAML contract version.
- `__pack_schema_version__`: Policy-pack manifest contract version.

When a serialized contract changes in a way that affects consumers, update the
corresponding schema version, JSON Schema, builders, examples, and tests
together.

## 3. Public API

The package root exports:

```python
from govlattice import (
    ComparisonOperator,
    PolicyDesigner,
    PolicyPackDesigner,
    PolicyReference,
    PolicyPackReader,
    PolicyReader,
    SeverityLevel,
)
```

Applications should use these public APIs. Internal node classes are
implementation details and should not be constructed directly.

Reader definitions and errors are also exported from the package root:

```python
from govlattice import (
    ConditionDefinition,
    PolicyDefinition,
    PolicyFileError,
    PolicyPackConsistencyError,
    PolicyPackDefinition,
    PolicyPackEntryDefinition,
    PolicyPackFileError,
    PolicyPackReadError,
    PolicyPackValidationError,
    PolicyReadError,
    PolicySyntaxError,
    PolicyValidationError,
    ReferenceDefinition,
    RequirementDefinition,
    SegmentDefinition,
    StateDefinition,
    UnsupportedPolicySchemaError,
    UnsupportedPolicyPackSchemaError,
)
```

## 4. Core Domain Model

A policy has the following logical structure:

```text
Policy
└── State (one or more)
    ├── Requirement (applies to the whole state)
    └── Segment (a conditional group within the state)
        ├── Condition
        └── Requirement (applies only to the segment)
```

### Policy

A policy is the top-level governance unit. One policy is exported as one YAML
file containing policy metadata and its states.

### State

A state represents a stage or form of a governed resource, for example:

- `raw_dataset`
- `validated_dataset`
- `training_dataset`
- `ai_system`

A policy may contain multiple states. State names must be non-empty strings.
Calling `.state()` again with an existing name reuses that state rather than
creating a duplicate.

### Segment

A segment represents a conditional group inside one state, such as `adult` or
`senior`. Use segments when different cohorts need different requirements.

A segment is not a nested state. The current implementation supports one
`.when_between()` condition per segment. Range boundaries are inclusive.

### Node

Nodes form the internal policy tree used by builders:

- `PolicyNode`
- `StateNode`
- `SegmentNode`
- `ConditionNode`
- `RequirementNode`
- Policy-pack nodes

Nodes are not part of the public domain-specific language.

## 5. Creating a Policy

The following example covers the main policy API:

```python
from govlattice import PolicyDesigner, PolicyReference, SeverityLevel

policy = (
    PolicyDesigner(
        policy_name="A10-health-policy",
        purpose="Ensure health datasets meet quality requirements.",
        enabled=True,
        severity=SeverityLevel.HIGH,
        tags=("health", "integration-test"),
        lifecycle_stages=("development", "validation"),
        references=(
            PolicyReference(
                title="Internal health data standard",
                url="https://example.com/health-standard",
            ),
        ),
        created_at="2026-07-01T09:00:00+07:00",
        updated_at="2026-07-27T17:30:00+07:00",
        owner="data-quality-team",
        agile_stage="testing",
        sprint="sprint-12",
    )
    .state("raw_dataset")
        .require_columns("id", "name", "age", "hba1c")
        .require_unique("id")
    .end()
    .state("validated_dataset")
        .segment("adult")
            .when_between("age", minimum=18, maximum=59)
            .require_missing_rate("hba1c", maximum=0.05)
            .require_range("hba1c", minimum=4.0, maximum=14.0)
            .require_metric("recall", 0.8)
            .require_metric(
                "false_positive_rate",
                0.1,
                operator=ComparisonOperator.LTE,
            )
            .require_column_value(
                "age",
                18,
                operator=ComparisonOperator.GTE,
            )
            .require_metrics(
                ("precision", "f1_score"),
                (0.75, 0.8),
            )
        .end()
        .segment("senior")
            .when_between("age", minimum=60, maximum=100)
            .require_missing_rate("hba1c", maximum=0.02)
        .end()
        .verify_overlap_range("age")
    .end()
)

output_path = policy.execute("health_policy.yml")
```

The fluent API uses `.end()` to return to the parent:

- `SegmentBuilder.end()` returns its `StateBuilder`.
- `StateBuilder.end()` returns its `PolicyDesigner`.

## 6. Policy Metadata

The current constructor is:

```python
PolicyDesigner(
    policy_name,
    *,
    purpose=None,
    enabled=True,
    severity=SeverityLevel.MEDIUM,
    tags=(),
    lifecycle_stages=(),
    references=(),
    created_at=None,
    updated_at=None,
    **metadata,
)
```

### Standard fields

- `policy_name`: The policy name and identity.
- `purpose`: An optional explanation of what the policy is intended to
  achieve.
- `enabled`: Whether the policy is active as metadata; must be a `bool`.
- `severity`: The policy's impact level.
- `tags`: Labels used for discovery and grouping.
- `lifecycle_stages`: Relevant lifecycle stages, such as development,
  validation, deployment, or operation.
- `references`: Optional external sources.
- `created_at`: Optional creation timestamp.
- `updated_at`: Optional update timestamp.

Supported severity levels are:

```python
SeverityLevel.INFO
SeverityLevel.LOW
SeverityLevel.MEDIUM
SeverityLevel.HIGH
SeverityLevel.CRITICAL
```

Severity is currently metadata for downstream consumers. The exporter does not
change its behavior based on severity.

### Custom metadata

Values passed through `**metadata` are written at the same policy level as the
standard fields:

```python
PolicyDesigner(
    "health-policy",
    owner="data-team",
    agile_stage="testing",
    review={"required": True, "approvers": ["governance-team"]},
)
```

Metadata supports:

- `None`
- Strings
- Booleans
- Finite integers and floats
- Lists and tuples
- Dictionaries whose keys are non-empty strings

Arbitrary Python objects, `NaN`, and infinity are rejected.

The following metadata keys are reserved:

```text
name, purpose, enabled, severity, tags, lifecycle_stages, references,
created_at, updated_at, states, schema_version
```

When provided, `purpose` must be a non-empty string. Surrounding whitespace is
removed. When omitted or set to `None`, it is not written to the YAML output.

### Timestamp behavior

GovLattice does not generate timestamps automatically. Explicit timestamps
keep generated output deterministic and prevent noisy Git diffs on every
execution.

A timestamp must:

- Be an ISO 8601 string.
- Include a time component.
- Include a timezone.
- Not place `created_at` after `updated_at`.

### Tags and lifecycle stages

These fields accept only lists or tuples of strings. Values are stripped of
surrounding whitespace and deduplicated while preserving their original order.

`lifecycle_stages` describes the lifecycle of the data, model, or system.
Team-specific Agile stages and sprint information belong in custom metadata.

### References

Create references with:

```python
PolicyReference(
    title="Regulation (EU) 2024/1689",
    url="https://eur-lex.europa.eu/...",
)
```

The URL must use HTTP or HTTPS and contain a host. References with duplicate
URLs are deduplicated, preserving the first entry.

## 7. Requirements

All current requirement methods are available on both states and segments.

### Required columns

```python
.require_columns("id", "name")
```

At least one column is required.

### Unique columns

```python
.require_unique("id")
```

This represents a column or set of columns that must be unique.

### Maximum missing rate

```python
.require_missing_rate("hba1c", maximum=0.05)
```

`maximum` must be between `0` and `1`.

### Numeric range

```python
.require_range("age", minimum=18, maximum=100)
```

`minimum` must not be greater than `maximum`.

### One model metric

```python
.require_metric("recall", 0.8)
```

The metric name is a domain-defined string, such as `recall`, `precision`, or
`f1_score`. The comparison value must be between `0` and `1`. The default
operator is `ComparisonOperator.GTE`, so the example means `recall >= 0.8`.

An explicit operator can be used for metrics where lower values are better:

```python
from govlattice import ComparisonOperator

.require_metric(
    "false_positive_rate",
    0.1,
    operator=ComparisonOperator.LTE,
)
```

For backward compatibility, the previous `minimum` keyword remains accepted:

```python
.require_metric("recall", minimum=0.8)
```

Do not pass both `value` and `minimum`.

### Column value comparison

```python
.require_column_value(
    "age",
    18,
    operator=ComparisonOperator.GTE,
)
```

This requirement compares a numeric column value against one numeric
threshold. It is available at both state and segment level.

Supported comparison operators are:

```python
ComparisonOperator.LT   # <
ComparisonOperator.LTE  # <=
ComparisonOperator.GT   # >
ComparisonOperator.GTE  # >=
```

Callers must pass a `ComparisonOperator`; raw strings such as `">="` are
rejected.

### Multiple model metrics

```python
.require_metrics(
    ("recall", "precision"),
    (0.8, 0.75),
)
```

Rules:

- `metrics` and `minimums` must be lists or tuples.
- At least one metric is required.
- Both collections must have the same length.
- Metric names must be unique within one requirement.
- Every minimum score must be between `0` and `1`.

`require_metrics()` retains its existing mapping form and does not currently
accept per-metric operators. Use multiple `require_metric()` calls when
different operators are needed.

The correct API names are `require_metric` and `require_metrics`. There are no
`metrice` or `metrices` aliases.

## 8. Segments and Overlap Verification

Example:

```python
(
    policy.state("validated_dataset")
    .segment("child")
        .when_between("age", 10, 17)
    .end()
    .segment("adult")
        .when_between("age", 18, 59)
    .end()
    .verify_overlap_range("age")
    .end()
)
```

`.verify_overlap_range("age")`:

- Checks only segments in the current state.
- Checks only `between` conditions for the selected column.
- Does not inspect another state.
- Does not detect gaps between ranges.
- Raises `ValueError` if no range exists for that column.
- Raises `OverlapRangeError` when ranges overlap.

Ranges are inclusive. Therefore, `10-20` and `20-30` overlap, while `10-20`
and `21-30` do not.

The verifier layer is designed to support additional verification strategies
without placing all cross-node logic in builders.

## 9. Policy YAML Contract

`execute()` creates a `.yml` or `.yaml` file. The output does not include a
`yaml-language-server` directive and does not include a `terms` field.

Example output:

```yaml
schema_version: "1.6.0"
policy:
  name: "A10-health-policy"
  purpose: "Ensure health datasets meet quality requirements."
  enabled: true
  severity: "high"
  tags:
    - "health"
  lifecycle_stages:
    - "validation"
  references: []
  owner: "data-quality-team"
  states:
    raw_dataset:
      requirements:
        - type: "require_columns"
          columns:
            - "id"
            - "name"
    validated_dataset:
      requirements: []
      segments:
        adult:
          when:
            type: "between"
            column: "age"
            minimum: 18
            maximum: 59
          requirements:
            - type: "require_metric"
              metric: "recall"
              operator: ">="
              value: 0.8
            - type: "require_column_value"
              column: "age"
              operator: ">="
              value: 18
            - type: "require_metrics"
              metrics:
                precision: 0.75
                f1_score: 0.8
```

The policy schema is:

```text
schemas/govlattice-policy.schema.json
```

It uses JSON Schema Draft 2020-12. The current policy schema version is
`1.6.0`.

## 10. Export Behavior

Examples:

```python
policy.execute("health_policy.yml")
policy.execute("health_policy.yaml")
policy.execute("health_policy.yml", output_dir="custom-policies")
```

The default output directory is `policies` under the current working
directory. GovLattice creates the directory if it does not exist and returns
the absolute output `Path`.

Output filename rules:

- The value must be a filename, not a path.
- `/` and `\` are rejected.
- The extension must be `.yml` or `.yaml`.

Files are written atomically. GovLattice first writes a temporary file in the
same directory and then replaces the destination with permissions `0644`.
This reduces the chance of leaving a partially written policy.

The serializer has no external YAML dependency. It uses JSON-compatible
scalars, which are valid YAML 1.2, and produces deterministic output.

## 11. Policy Packs

A policy pack groups multiple policies under one regulation, standard, or
governance framework, such as the EU AI Act. Policies remain separate files so
they are easier to review, version, and reuse.

Example:

```python
from govlattice import (
    PolicyDesigner,
    PolicyPackDesigner,
    SeverityLevel,
)

data_policy = (
    PolicyDesigner(
        "data-governance",
        purpose="Ensure training data meets governance requirements.",
        severity=SeverityLevel.HIGH,
        lifecycle_stages=("development", "validation"),
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
        enabled=True,
        jurisdiction=("EU",),
        tags=("ai-governance", "regulatory"),
        framework="Regulation (EU) 2024/1689",
    )
    .add_policy(data_policy)
    .verify_unique_policy_ids()
    .verify_schema_versions()
    .verify_policy_references()
)

manifest_path = pack.execute("eu-ai-act")
```

The constructor is:

```python
PolicyPackDesigner(
    pack_id,
    name,
    version,
    *,
    purpose=None,
    enabled=True,
    jurisdiction=(),
    tags=(),
    **metadata,
)
```

The pack ID and execution directory name must match:

```text
[A-Za-z0-9][A-Za-z0-9._-]*
```

A policy added to a pack must also have a file-safe `policy_name`.

Pack metadata supports the same value types as policy metadata. These keys are
reserved:

```text
id, name, version, purpose, enabled, jurisdiction, tags, policies,
pack_schema_version
```

Pack `purpose` follows the same rules as policy `purpose`: it is optional,
trimmed, must not be empty when supplied, and is omitted from the manifest when
its value is `None`. `purpose` is also a reserved pack metadata key.

### Pack verifiers

- `verify_unique_policy_ids()` rejects duplicate policy IDs.
- `verify_schema_versions()` verifies that a policy schema version is defined.
- `verify_policy_references()` validates every policy reference URL.

`execute()` runs all three verifiers automatically. Calling them explicitly is
useful when validation should fail before export begins.

### Pack output structure

```text
policies/
└── eu-ai-act/
    ├── manifest.yml
    └── policies/
        ├── data-governance.yml
        └── human-oversight.yml
```

Example manifest:

```yaml
pack_schema_version: "1.2.0"
policy_pack:
  id: "eu-ai-act"
  name: "EU AI Act"
  version: "1.0.0"
  purpose: "Group policies supporting EU AI Act compliance."
  enabled: true
  jurisdiction:
    - "EU"
  tags:
    - "ai-governance"
  policies:
    - id: "data-governance"
      file: "policies/data-governance.yml"
      enabled: true
      severity: "high"
      schema_version: "1.6.0"
```

The pack schema is:

```text
schemas/govlattice-policy-pack.schema.json
```

## 12. Reading Policies

`PolicyReader` safely loads one policy YAML file and returns an immutable,
typed `PolicyDefinition`:

```python
from govlattice import PolicyReader

policy = PolicyReader.read("policies/health_policy.yml")

print(policy.name)
print(policy.purpose)
print(policy.severity)

for state_id, state in policy.states.items():
    print(state_id, state.requirements)
```

The read pipeline is:

```text
YAML file
    ↓
PolicyYamlLoader
    └── PyYAML safe loader with duplicate-key rejection
    ↓
PolicyValidator
    ├── Schema-version check
    └── JsonSchemaValidator
            └── JSON Schema Draft 2020-12 validation
    ↓
PolicyDefinitionFactory
    └── Immutable PolicyDefinition
```

Reader behavior:

- Accepts string and `Path` inputs ending in `.yml` or `.yaml`.
- Rejects missing paths, directories, invalid extensions, and files larger
  than 1 MiB.
- Reads UTF-8 only.
- Uses a customized PyYAML `SafeLoader`.
- Rejects duplicate keys and unsafe YAML object tags.
- Validates date-time formats and all other policy schema rules using
  `jsonschema`.
- Supports only `govlattice.__schema_version__`, currently `1.6.0`.
- Converts severity strings into `SeverityLevel`.
- Converts requirement operators into `ComparisonOperator`.
- Separates custom metadata from standard policy fields.
- Recursively freezes mappings as read-only mapping proxies and lists as
  tuples.

Returned read models are frozen, slotted dataclasses:

```text
PolicyDefinition
├── ReferenceDefinition
└── StateDefinition
    ├── RequirementDefinition
    └── SegmentDefinition
        ├── ConditionDefinition
        └── RequirementDefinition
```

Reader error hierarchy:

```text
PolicyReadError
├── PolicyFileError
├── PolicySyntaxError
├── PolicyValidationError
└── UnsupportedPolicySchemaError
```

`PolicyReader` does not return `PolicyDesigner`. The designer is a mutable
construction API, while reader definitions represent validated, read-only
policy data for inspection and future execution.

### Reading policy packs

`PolicyPackReader` safely loads a pack manifest and every referenced policy:

```python
from govlattice import PolicyPackReader

pack = PolicyPackReader.read(
    "policies/eu-ai-act/manifest.yml"
)

for policy_id, entry in pack.policies.items():
    print(policy_id, entry.policy.states)
```

The pack read pipeline is:

```text
manifest.yml
    ↓
PolicyPackYamlLoader
    ↓
PolicyPackValidator
    └── JsonSchemaValidator
    ↓
Secure policy-path resolution
    ↓
PolicyReader for every entry
    ↓
Cross-file consistency validation
    ↓
PolicyPackDefinitionFactory
    └── Immutable PolicyPackDefinition
```

Pack reader behavior:

- Eagerly loads all policies before returning.
- Requires policy paths under the pack's `policies/` directory.
- Rejects absolute paths, `..`, paths outside the pack, and symlink escapes.
- Rejects duplicate policy IDs and duplicate resolved file references.
- Verifies that manifest ID, enabled, severity, and policy schema version
  match the loaded policy.
- Returns frozen, slotted `PolicyPackDefinition` and
  `PolicyPackEntryDefinition` objects with recursively read-only metadata.

Pack reader error hierarchy:

```text
PolicyPackReadError
├── PolicyPackFileError
├── PolicyPackValidationError
├── PolicyPackConsistencyError
└── UnsupportedPolicyPackSchemaError
```

Schema migrations, remote URL loading, lazy policy loading, and policy editing
are outside the current reader scope.

## 13. Architecture and Responsibilities

The main data flow is:

```text
User fluent API
    ↓
Designer / Builder
    ↓
Internal node tree
    ├── Verifier
    └── YAML Builder
            ↓
      Atomic file helper

Policy YAML
    ↓
PolicyReader
    ↓
Immutable definitions

Pack manifest
    ↓
PolicyPackReader
    ↓
Immutable pack and policy definitions
```

Directory responsibilities:

```text
govlattice/
├── __init__.py          Public exports and version constants
├── enum/
│   ├── comparison.py    ComparisonOperator enum
│   └── severity.py      SeverityLevel enum
├── error/
│   ├── policy_read_error.py    PolicyReader exception hierarchy
│   ├── policy_pack_read_error.py  PolicyPackReader exception hierarchy
│   └── schema_validation_error.py  Reusable schema-validation error
├── model/
│   ├── policy_definition.py       Frozen policy dataclasses
│   ├── policy_pack_definition.py  Frozen pack dataclasses
│   └── immutable.py               Recursive immutable-value helper
├── reader/
│   ├── policy_reader.py            Reader workflow orchestration
│   ├── policy_pack_reader.py       Pack reader orchestration and security
│   ├── policy_yaml_loader.py       Safe file and YAML loading
│   ├── policy_pack_yaml_loader.py  Safe manifest loading
│   ├── policy_definition_factory.py  Policy read-model construction
│   └── policy_pack_definition_factory.py  Pack read-model construction
├── validator/
│   ├── json_schema_validator.py    Reusable JSON Schema validation
│   ├── policy_validator.py         Policy contract checks
│   └── policy_pack_validator.py    Pack contract checks
├── designer/            Top-level policy and pack APIs
├── builder/             Fluent builders and YAML serializers
├── nodes/               Internal domain representation
├── verifier/            Policy and pack validation rules
└── utils/helper/        Reusable filesystem helpers

schemas/                  JSON Schema contracts
dev/                      Executable usage examples
tests/                    unittest test suite
policies/                 Generated output; ignored by Git
context/project.md        This project-wide reference
```

Responsibility boundaries:

- A Designer starts and completes a policy or pack workflow.
- A Builder implements the fluent DSL and adds nodes.
- A Node stores data and validates object-level invariants.
- A Verifier validates relationships across multiple nodes.
- A YAML Builder serializes the node tree deterministically.
- File helpers validate paths, create directories, and perform atomic writes.
- A Validator checks serialized contracts independently of reading or
  designing policies.

`JsonSchemaValidator` is reusable infrastructure. It accepts a schema path,
validates arbitrary mapping documents, formats field-level errors, and caches
the compiled validator by resolved schema path. `PolicyValidator` adds
policy-specific schema-version handling and converts generic schema failures
into `PolicyValidationError`.

The existing `verifier/` package remains separate:

- `validator/` checks serialized document contracts.
- `verifier/` checks semantic relationships between domain nodes.

## 14. Design Decisions

### Policy names are not duplicated as `self.policy_id`

`policy_name` is the policy identity through the base `Designer` and is also
used as the policy ID in a pack. The implementation does not keep an
unnecessary duplicate string in `self.policy_id`.

### States and segments have different meanings

A state represents a stage or form of a resource. A segment represents a
conditional cohort within that state. Cohorts such as age groups therefore
use segments rather than nested states.

### Lifecycle stage is first-class; Agile data is metadata

`lifecycle_stages` describes where a policy applies in the data, model, or
system lifecycle. Agile stages and sprints are team-specific workflow data and
belong in custom metadata.

### Timestamps are explicit

The package does not generate `created_at` or `updated_at` automatically.
Automatic timestamps would change generated YAML on every execution and
create noisy Git diffs.

### Packs reference separate policy files

A pack creates a manifest and separate policy files instead of placing every
policy in one large YAML document. This improves reviewability and supports
future policy reuse.

### Internal objects are memory-conscious

Internal model classes use `__slots__` and avoid storing duplicate fields
without a clear reason.

### Python typing favors compatibility

The code uses `typing.Union`, `Optional`, and quoted forward references instead
of syntax that requires Python 3.10 or newer, such as `A | B`. It also avoids
depending on `typing.Self`, preventing Pylance issues when a project targets an
older Python version.

### Policy reading is separate from policy design

`PolicyDesigner` builds mutable policy trees. `PolicyReader` returns immutable
definitions after schema validation. This boundary prevents accidental edits
and prepares the project for a future execution layer.

### YAML reading uses established safe parsers

The writer remains dependency-free, but the reader uses PyYAML rather than a
custom YAML parser. JSON Schema validation uses `jsonschema` so the serialized
schema remains the validation source of truth.

## 15. Local Development

The repository contains a `.venv` at its root. Run commands from the project
root:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python dev/dev_policy_desinger.py
python dev/dev_pack_eu_ai_act.py
python dev/dev_policy_reader.py
```

Without activating the environment:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The development scripts add the project root to `sys.path`, allowing them to
run directly without raising:

```text
ModuleNotFoundError: No module named 'govlattice'
```

Current examples:

- `dev/dev_policy_desinger.py`: Multiple states, segments, overlap checks,
  custom metadata, and metric requirements.
- `dev/dev_pack_eu_ai_act.py`: Policy packs, severity, lifecycle stages,
  references, and pack verification.
- `dev/dev_policy_reader.py`: Safe loading and inspection of a generated
  policy.
- `dev/dev_policy_pack_reader.py`: Secure loading and inspection of a
  generated policy pack.

The existing filename `dev_policy_desinger.py` contains the spelling
`desinger`; this section intentionally reflects the current repository name.

Runtime dependencies:

```text
PyYAML>=6.0,<7
jsonschema>=4.0,<5
```

## 16. Testing Expectations

The project uses the standard-library `unittest` framework.

Changes to behavior should test at least:

- The public fluent API's happy path.
- Invalid types and empty values.
- Boundary values such as scores `0` and `1`.
- Inclusive range behavior.
- Deterministic YAML output.
- Path traversal and invalid extensions.
- Atomic output behavior.
- Version agreement among constants, YAML builders, and JSON Schemas.
- Single-policy and policy-pack export.
- Safe policy reading, duplicate-key rejection, schema validation, immutable
  definitions, and unsupported schema versions.
- Safe policy-pack reading, path and symlink containment, cross-file
  consistency, eager loading, and duplicate detection.

The generated `policies/` directory is ignored by Git because it is user
output, not source code.

## 17. Current Limitations and Deferred Ideas

The following features are not implemented and must not be presented as
available:

- A runtime engine that evaluates data or models from YAML.
- Reading older policy schemas through migrations.
- Nested segments.
- Conditions other than `between`.
- Multiple Boolean conditions in one segment.
- Overlap verification across states.
- Gap verification.
- Automatic timestamps.
- Online availability checks for references.
- `applies_when`.
- `source_refs` separate from `references`.
- `depends_on` relationships between policies.
- Lifecycle enforcement.
- Severity-dependent execution behavior.
- Per-metric operators in `require_metrics()`.
- Pack dependency resolution or a policy reuse registry.
- A command-line interface.
- Published-package build configuration.

These are extension candidates only. Discuss their public APIs and serialized
contracts before changing the project structure or schemas.

## 18. Change Guidelines

When implementing a new feature:

1. Keep the fluent API readable and aligned with domain terminology.
2. Do not expose internal nodes unless necessary.
3. Keep validation close to object invariants; use verifiers for cross-node
   rules.
4. Do not introduce a new directory structure without a concrete need. Confirm
   architectural changes with the project owner first.
5. Preserve deterministic output and atomic file writes.
6. Add or update tests alongside behavior.
7. When the YAML contract changes, update version constants, JSON Schemas,
   builders, examples, and tests together.
8. Update this document to describe only behavior that has been implemented.

## 19. Source-of-Truth Priority

If project information conflicts, use this order:

1. Passing tests and current public behavior.
2. JSON Schemas for serialized contracts.
3. Public Designer and Builder APIs.
4. This document.
5. Generated example files.

If implementation changes make this document inaccurate, update
`context/project.md` in the same change.
