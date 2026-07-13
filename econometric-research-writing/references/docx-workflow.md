# DOCX Workflow

This reference is a long-term skill resource for Word, OMML, rendering, and QA work for econometric research papers, course reports, and economics/management empirical documents.

## Table Of Contents

- Formula Strategy
- OMML Checks
- Style and Layout Checks
- Citation And Reference Checks
- Rendering
- DOCX Builder Options
- File Status Language

## Formula Strategy

Generate or edit formulas as Word-native OMML/OOXML inside the `.docx` using the following workflow:

1. Generate or edit formulas as Word-native OMML/OOXML inside the `.docx`.
2. Preserve existing document structure, tables, figures, references, and styles.
3. Save as a new formal version unless the user explicitly asks to overwrite.
4. Render the `.docx` and inspect pages before delivery.
5. Clean temporary scripts and render outputs.

## OMML Checks

When formulas are in scope:

- Count `<m:oMath` before and after.
- Ensure inline formulas are not converted to plain Unicode when Word-native math is required.
- Check common course-report inline formulas carefully: summations, lag operators, unit-root statistics, VAR coefficient matrices, fixed effects restrictions, kernel weights, bandwidth rates, time-varying coefficients such as `β(t)` or `β(τ)`, and panel constraints such as `Σ_i α_i = 0`.
- Use `≤` and `∈` rather than ASCII-only `<=` and `in` when rendering math in final prose/formulas.
- Avoid OMML `m:nary` structures with an empty operand; Word shows these as empty square placeholder boxes.
- If using a summation with limits, either provide the operand correctly or use a scripted `∑` formula object that renders without empty boxes.

## Style and Layout Checks

After document edits:

- Confirm headings are black, not Word's default blue heading color.
- Preserve the supplied template's Latin and East Asian font mappings unless the user requests an override. For a net-new document without a template, apply the skill's Times New Roman default consistently through document styles rather than hard-coding every run.
- Use three-line tables as the default for economics/management papers and course reports: top rule, header-bottom rule, and bottom rule only; no vertical borders and no full grid lines unless the user explicitly requests grid tables or the source document already requires them.
- For regression tables, summary-statistics tables, robustness tables, and method-comparison tables, keep notes below the table rather than adding extra boxed rows when possible.
- For tables and figures, follow `tables-figures-style.md`: self-contained captions/legends, readable figure labels, source notes after other notes, and text callouts before or near each object.
- Keep figure data colors when they carry meaning; only title/labels should be normalized if color is a formatting problem.
- If numeric citations or note markers are required, use true Word superscript runs (`w:vertAlign w:val="superscript"`), not plain text markers such as `[1]`, `^1`, or Unicode superscript as the main representation.
- Confirm page count whenever a prior authoritative version or a submission requirement establishes an expected count.
- Check no blank pages, clipped equations, overflowed tables, missing captions, or broken references.

## Citation And Reference Checks

When citations are in scope:

- Follow `literature-citation-workflow.md` before adding or formatting references.
- Verify reference metadata before including it in the final reference list.
- Confirm every in-text citation has a reference-list entry and every reference-list entry is cited.
- For Word superscript citations, run `scripts/check_docx_integrity.py` and confirm `superscript_run_count` is positive when superscript markers are expected.
- Inspect `plain_numeric_citation_markers_preview`; if it contains citation markers that should be superscript, revise the document.

## Rendering

Use the available document rendering toolchain when layout matters. Prefer the skill wrapper because it can use a configured Python runtime and prepend configured native binaries:

```bash
python3 scripts/render_validate_docx.py output.docx --output-dir .qa/econ_docx_render
```

The wrapper discovers the `documents` renderer at runtime. It checks `DOCX_RENDER_SCRIPT` or `DOCUMENTS_RENDER_SCRIPT`, searches directories listed in `DOCUMENTS_SKILL_ROOT` or `DOCUMENT_RENDERER_SEARCH_ROOTS`, and then searches versioned bundled Codex plugin caches. Load the workspace dependencies first when a bundled Python/runtime is available. Missing input, missing renderer, renderer failure, or zero newly rendered page images is a failed QA step with a nonzero exit status. The wrapper removes stale `page-*.png` files from the designated QA directory before rendering.

Render outputs are temporary QA artifacts. Put them in a clearly temporary working directory such as `.qa/econ_docx_render` and remove them after inspection unless the user asks to keep them.

## DOCX Builder Options

`scripts/build_paper_docx.py` preserves a supplied template's styles by default. Use `--apply-default-style` only when the output should override the template with the built-in Times New Roman paper layout.

Validate structured builder input against `schemas/paper-docx.schema.json`. Start from the runnable `examples/paper-docx.example.json` when creating a new input; it demonstrates every core content type without depending on an external figure file.

For tables with spanned headers or grouped categories, table specs may include `header_merges` or `merges` supporting both horizontal and vertical merges:

- **Horizontal Merge (Row-based)**:
  `{"row": 0, "start_col": 1, "end_col": 2}` or list `[row, start_col, end_col]`.
- **Vertical Merge (Column-based)**:
  `{"col": 0, "start_row": 1, "end_row": 3}` or list `[col, start_row, end_row, "vertical"]`.

```json
{
  "type": "table",
  "caption": "Table 2. Baseline estimates",
  "rows": [
    ["", "Outcome A", "", "Outcome B", ""],
    ["", "(1)", "(2)", "(3)", "(4)"]
  ],
  "header_merges": [
    {"row": 0, "start_col": 1, "end_col": 2},
    {"row": 0, "start_col": 3, "end_col": 4}
  ]
}
```

Set `header_rows` to the number of header rows when a table has a grouped or multirow header. The three-line formatter places the middle rule below the final header row, not mechanically below row 1. When `header_rows` is omitted, grouped `header_merges` are used only as a conservative inference; explicit configuration is preferred.

Plain table strings always remain text, including identifiers such as `firm_id`. Request Word-native math explicitly for a cell:

```json
{"text": "beta_1", "math": true}
```

The shorthand `{"math": "beta_1"}` is also accepted. Unsupported formula commands or malformed groups fail explicitly instead of silently degrading into misleading text.

Three-line formatting remains the default unless `style` is explicitly set to `grid`.
Use `column_widths_inches` and `column_alignments` when a table needs stable
geometry at final page size. Header rows repeat by default; set
`"repeat_header": false` only when repetition is intentionally disabled.

For enforceable structural QA, `scripts/check_docx_integrity.py` supports minimum-count assertions such as `--min-omml`, `--min-tables`, `--min-media`, `--min-headings`, and `--min-superscript-runs`, plus `--require-three-line-tables`, `--forbid-grid-tables`, `--fail-on-plain-citations`, `--fail-on-nonblack-headings`, and `--require-clean-core-styles`. Heading-color QA checks both style definitions and paragraph/run direct formatting. The last flag requires explicit black Title/Subtitle/Caption styles and no Title paragraph-border residue. Border QA inspects explicit table and cell borders rather than relying only on the table style name.

## File Status Language

In final responses after document generation or cleanup, explicitly state:

- Which file is the final authoritative version.
- Which files are formal archives.
- Which files were temporary and were removed.
- Which reproducibility materials were intentionally kept.

Examples:

- A file named `*_final.docx` or explicitly selected by the user is a final authoritative version.
- A version named `*_OMML.docx`, `*_style_revised.docx`, or `*_method_revised.docx` can be a formal archive if it marks a meaningful version boundary.
- Scratch scripts, render folders, temporary PDFs/PNGs, smoke-test documents, and Word lock files are temporary.
