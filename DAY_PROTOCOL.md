# DAY PROTOCOL — BCI-CALIB

Operational development workflow for reproducible research engineering.

---

# 1. Open Project

Update local repository:

```bash
git checkout dev
git pull origin dev
```

Synchronize environment:

```bash
just sync
```

---

# 2. Create Branch

Documentation:

```bash
git checkout -b docs/name
```

Feature:

```bash
git checkout -b feature/name
```

Fix:

```bash
git checkout -b fix/name
```

---

# 3. During Development

Rules:

- Core logic belongs in `src/`
- Notebooks are only for exploration
- Domain layer must not depend on infrastructure
- Preserve reproducibility

---

# 4. After Modifying Code

Run autofix:

```bash
just fix
```

Format code:

```bash
just format
```

Run type checking:

```bash
just typecheck
```

Run tests:

```bash
just test
```

---

# 5. Before Commit

Run full validation pipeline:

```bash
just all
```

Run security checks:

```bash
just security
```

Dependency audit:

```bash
just audit
```

Generate SBOM:

```bash
just sbom
```

---

# 6. Commit Convention

Examples:

```bash
git commit -m "feat: add dynamic calibration pipeline"
```

```bash
git commit -m "docs: update ADR documentation"
```

```bash
git commit -m "fix: resolve CI typing issue"
```

---

# 7. Push

```bash
git push origin branch-name
```

---

# 8. Pull Request Checklist

Required:

- CI green
- Ruff passing
- mypy passing
- tests passing
- no secrets
- documentation updated when needed
- ADR added for architectural decisions

---

# Scientific Validation Rules

All calibration modifications must evaluate:

- Expected Calibration Error (ECE)
- Brier Score
- Calibration Curve

---

# Architecture Constraints

Forbidden:

- infrastructure imports inside `domain/`
- core logic inside notebooks
- direct edits to `uv.lock`
- secrets committed to git

---

# Governance References

- SECURITY.md
- docs/adr/
- README.md
