# Econometric Research Writing

An agent skill for professional economics and management empirical research workflows.

It supports:

- Econometric dataset profiling and model-readiness checks.
- Method selection for panel, time-series, causal inference, RDD, matching, IPW, staggered DiD, GARCH, Markov-switching, panel VAR, and spatial panel designs.
- Economics/management paper writing with bounded causal language.
- Literature search and citation integrity workflows.
- Publication-style Word document generation with editable OMML formulas, three-line tables, source notes, figure/table QA, and superscript citation markers.

## Structure

```text
econometric-research-writing/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── econ-paper-template.docx
├── references/
│   ├── data-analysis-workflow.md
│   ├── docx-workflow.md
│   ├── econ-writing-style.md
│   ├── empirical-workflow.md
│   ├── iv-causal-methods.md
│   ├── literature-citation-workflow.md
│   ├── method-selection.md
│   ├── panel-methods.md
│   ├── rdd-matching-methods.md
│   ├── tables-figures-style.md
│   └── time-series-methods.md
└── scripts/
    ├── build_paper_docx.py
    ├── check_docx_integrity.py
    ├── omml_math.py
    ├── profile_econ_dataset.py
    ├── render_validate_docx.py
    └── verify_references.py
```

## Usage

Install or copy the folder into an agent skill directory that supports `SKILL.md`-based skills.

Run helper scripts from the skill root, for example:

```bash
python3 scripts/profile_econ_dataset.py data.csv --out profile.md --json-out profile.json
python3 scripts/build_paper_docx.py paper.json paper.docx --template assets/econ-paper-template.docx
python3 scripts/check_docx_integrity.py paper.docx
python3 scripts/verify_references.py references.json --out-json verification.json --out-enriched-json references_clean.json
```

DOCX rendering depends on an external document renderer. Configure it with one of:

- `DOCX_RENDER_SCRIPT`
- `DOCUMENTS_RENDER_SCRIPT`
- `DOCUMENTS_SKILL_ROOT`
- `DOCUMENT_RENDERER_SEARCH_ROOTS`

## Design Principles

- Do not invent citations, papers, DOIs, datasets, or empirical evidence.
- Treat fixed effects, VAR, threshold, and flexible nonparametric estimates as association unless a credible identification design is stated.
- Use three-line tables by default for economics and management empirical outputs.
- Keep model interpretation tied to variable meaning, economic pathways, and the identification threat model.
- Keep generated Word formulas editable as Office Math where formulas matter.

## License

MIT License. See [LICENSE](LICENSE).
