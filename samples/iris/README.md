# Iris Sample Policies

This directory keeps both the policy source and generated YAML together so
the examples are self-contained and easy to review.

Generate or refresh the policy files from the repository root:

```bash
.venv/bin/python samples/iris/create_policies.py
```

The command writes:

```text
samples/iris/iris-dataset-quality.yml
samples/iris/iris-model-quality.yml
```

`iris-dataset-quality.yml` validates required columns, missing values, and
reasonable measurement ranges. `iris-model-quality.yml` defines minimum
accuracy, macro precision, macro recall, and macro F1 thresholds.

The measurement ranges intentionally extend beyond the exact minimum and
maximum values in the canonical Iris dataset. This avoids rejecting a new but
reasonable observation merely because it falls outside the original sample.

## Run the policy engine

Install the sample dependencies:

```bash
.venv/bin/python -m pip install -r requirements-iris.txt
```

Run the end-to-end example:

```bash
.venv/bin/python samples/iris/run_policy_engine.py
```

The example:

1. Loads the canonical Iris dataset from scikit-learn.
2. Converts it to a policy-compatible Pandas DataFrame.
3. Enforces `iris-dataset-quality.yml`.
4. Creates a reproducible stratified train/test split.
5. Trains a scaled logistic-regression classifier.
6. Calculates accuracy, macro precision, macro recall, and macro F1.
7. Enforces `iris-model-quality.yml` using the calculated metrics.

The workflow continues only when both active policies pass.
