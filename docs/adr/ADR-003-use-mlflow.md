
---

# ADR-003 — Use MLflow for Experiment Tracking

```md
# ADR-003 — Use MLflow for Experiment Tracking

## Status

Accepted

---

## Context

The project requires systematic tracking of:

- experiments
- calibration metrics
- hyperparameters
- datasets
- model artifacts
- physiological preprocessing parameters

Manual experiment tracking through:
- spreadsheets,
- notebooks,
- local logs

is error-prone and harms reproducibility.

The project also requires future support for:

- benchmark comparison
- calibration studies
- auditability
- scientific replication

---

## Decision

Adopt MLflow as the experiment tracking platform.

MLflow responsibilities:

- metric logging
- artifact storage
- parameter tracking
- run comparison
- experiment reproducibility

Initial usage scope:

- local tracking server
- local artifact storage
- calibration experiment tracking

---

## Rationale

MLflow provides:

- framework-agnostic experiment tracking
- lightweight setup
- strong Python ecosystem integration
- compatibility with scientific workflows
- future scalability to remote tracking

The solution integrates well with:
- scikit-learn
- PyTorch
- MOABB
- custom calibration pipelines

---

## Consequences

### Positive

- reproducible experiments
- centralized metrics
- easier benchmark analysis
- experiment lineage
- better research governance

### Negative

- additional dependency weight
- artifact storage management
- local storage growth over time

---

## Alternatives Considered

### TensorBoard

Rejected because:
- stronger DL focus
- weaker generic experiment management

### Weights & Biases

Rejected because:
- cloud-first workflow
- external SaaS dependency
- less suitable for offline/local-first research

### CSV/manual logging

Rejected because:
- weak reproducibility
- difficult comparison
- high operational overhead

---

## References

- MLflow official documentation
- Zaharia et al. — Accelerating the Machine Learning Lifecycle with MLflow
- Google Rules of ML
- NIST AI RMF
