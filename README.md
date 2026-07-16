# Econometric Research Writing Skill

Reusable `SKILL.md`-based agent skill for econometric analysis, economics/management empirical writing, citation integrity, and Word document production.

## Overview

An end-to-end skill for professional economics and management empirical research. It supports:

- Econometric dataset profiling and model-readiness checks.
- Evidence-first research grilling with one or more dependency-aware questions, recommended answers, knowledge-adaptive explanations, and an explicit implementation gate.
- Agent-decided variable roles based on data values, names, timing, codebook evidence, and the research question, with economic meaning checks, mechanism-path mapping, and causal-language boundaries.
- Method selection for panel, time-series, causal inference, RDD, matching, IPW, staggered DiD, GARCH, Markov-switching, panel VAR, and spatial panel designs.
- Literature search, citation provenance, and reference-integrity workflows with a strict no-fabrication rule.
- Economics/management paper drafting, empirical-strategy writing, results interpretation, robustness framing, and polished academic prose.
- Publication-style Word document generation with editable OMML formulas, three-line tables, source notes, figure/table QA, and superscript citation markers.

## Repository Layout

```text
.
├── econometric-research-writing/
│   ├── SKILL.md
│   ├── agents/
│   │   └── openai.yaml
│   ├── assets/
│   │   └── econ-paper-template.docx
│   ├── references/
│   └── scripts/
├── scripts/
│   └── validate_repository.py
├── requirements.txt
└── LICENSE
```

The skill directory intentionally contains only files needed by a `SKILL.md`-compatible agent runtime: core instructions, optional UI metadata, references, scripts, and reusable assets. Repository-level documentation and validation live at the repository root.

## Install

Clone the repository and copy the skill folder into the skill directory used by your agent runtime:

```bash
git clone https://github.com/lixinglong27/econometric-research-writing.git
cp -R econometric-research-writing/econometric-research-writing "$AGENT_SKILLS_DIR/econometric-research-writing"
```

Replace `AGENT_SKILLS_DIR` with the directory your runtime uses for local skills.

## Use Helper Scripts

Install the Python dependencies when you want to run the bundled helper scripts directly:

```bash
python3 -m pip install -r requirements.txt
```

Example commands from the repository root:

```bash
python3 econometric-research-writing/scripts/profile_econ_dataset.py data.csv --out profile.md --json-out profile.json
python3 econometric-research-writing/scripts/run_empirical_analysis.py data.csv --roles-json roles.json --output-dir results
python3 econometric-research-writing/scripts/build_paper_docx.py paper.json paper.docx --template econometric-research-writing/assets/econ-paper-template.docx
python3 econometric-research-writing/scripts/check_docx_integrity.py paper.docx
python3 econometric-research-writing/scripts/verify_references.py references.json --out-json verification.json --out-enriched-json references_clean.json
```

DOCX rendering is optional and depends on an external document renderer. The skill supports renderer discovery through generic document-rendering environment variables documented in `econometric-research-writing/references/docx-workflow.md`.

## Validate

Run the lightweight repository checks:

```bash
python3 scripts/validate_repository.py
```

Run full smoke tests after installing dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_repository.py --full
```

The full validation compiles helper scripts, checks for local-path leaks, verifies the DOCX template structure, profiles a small panel dataset, generates a paper DOCX with an editable formula and three-line table, and inspects the result for citation/table/style issues.

## Responsible Use

- Treat the skill as a research and writing assistant, not a substitute for econometric judgment. Review model choices, identifying assumptions, and result interpretation before relying on outputs.
- Verify data rights, privacy constraints, and institutional rules before using confidential or restricted datasets with any agent runtime.
- Treat literature and citation outputs as source-backed only after verification. If a paper, DOI, dataset, or claim cannot be verified, do not cite it as fact.
- Inspect generated Word documents before submission, especially formulas, table notes, source notes, citations, and figure placement.
- For repository maintenance and contribution standards, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).
