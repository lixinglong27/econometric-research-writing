# Contributing

This repository contains a reusable `SKILL.md`-based agent skill. Keep changes focused and easy to validate.

## Before Opening A Pull Request

Run:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_repository.py --full
```

## Standards

- Keep each skill directory limited to `SKILL.md`, `agents/`, `references/`, `scripts/`, and `assets/` unless a runtime need justifies another file.
- Put repository-facing documentation at the repository root.
- Do not commit local absolute paths, temporary QA renders, cache files, or personal environment details.
- Do not add fabricated citations, unverifiable references, or unsupported empirical claims.
- Prefer deterministic helper scripts for fragile document, citation, or data-analysis behavior.
