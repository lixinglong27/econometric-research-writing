#!/usr/bin/env python3
import argparse
import json
import py_compile
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "econometric-research-writing"
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".txt", ".json"}
FORBIDDEN_TEXT = [
    "/" + "Users" + "/",
    "file:" + "//",
    "xing" + "longli",
    "非线性" + "时间序列",
]


def fail(message):
    raise AssertionError(message)


def read_text(path):
    return path.read_text(encoding="utf-8")


def iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE"}:
            yield path


def check_required_layout():
    required = [
        ROOT / "README.md",
        ROOT / "LICENSE",
        ROOT / "requirements.txt",
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "agents" / "openai.yaml",
        SKILL_DIR / "assets" / "econ-paper-template.docx",
        SKILL_DIR / "references" / "method-selection.md",
        SKILL_DIR / "references" / "time-series-methods.md",
        SKILL_DIR / "references" / "panel-methods.md",
        SKILL_DIR / "references" / "iv-causal-methods.md",
        SKILL_DIR / "references" / "rdd-matching-methods.md",
        SKILL_DIR / "references" / "data-analysis-workflow.md",
        SKILL_DIR / "references" / "empirical-workflow.md",
        SKILL_DIR / "references" / "econ-writing-style.md",
        SKILL_DIR / "references" / "tables-figures-style.md",
        SKILL_DIR / "references" / "literature-citation-workflow.md",
        SKILL_DIR / "references" / "docx-workflow.md",
        SKILL_DIR / "scripts" / "build_paper_docx.py",
        SKILL_DIR / "scripts" / "check_docx_integrity.py",
        SKILL_DIR / "scripts" / "omml_math.py",
        SKILL_DIR / "scripts" / "profile_econ_dataset.py",
        SKILL_DIR / "scripts" / "run_empirical_analysis.py",
        SKILL_DIR / "scripts" / "render_validate_docx.py",
        SKILL_DIR / "scripts" / "verify_references.py",
        SKILL_DIR / "tests" / "test_regressions.py",
    ]
    for path in required:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    for extra in ["README.md", "LICENSE", ".gitignore"]:
        path = SKILL_DIR / extra
        if path.exists():
            fail(f"repository-level file should not be inside skill directory: {path.relative_to(ROOT)}")


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    try:
        _, raw, body = text.split("---", 2)
    except ValueError as exc:
        raise AssertionError("SKILL.md frontmatter is not closed") from exc
    fields = {}
    for line in raw.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields, body


def check_skill_metadata():
    fields, body = parse_frontmatter(read_text(SKILL_DIR / "SKILL.md"))
    if set(fields) != {"name", "description"}:
        fail(f"SKILL.md frontmatter must contain only name and description, got {sorted(fields)}")
    if fields["name"] != "econometric-research-writing":
        fail("unexpected skill name")
    if len(fields["description"]) < 200:
        fail("description is too short to provide useful trigger coverage")
    if len(body.splitlines()) > 500:
        fail("SKILL.md body is too long; move details into references")

    agent_yaml = read_text(SKILL_DIR / "agents" / "openai.yaml")
    for token in ["interface:", "display_name:", "short_description:", "default_prompt:"]:
        if token not in agent_yaml:
            fail(f"agents/openai.yaml missing {token}")


def check_no_forbidden_text():
    for path in iter_text_files():
        text = read_text(path)
        for token in FORBIDDEN_TEXT:
            if token in text:
                fail(f"forbidden text {token!r} in {path.relative_to(ROOT)}")


def check_docx_template():
    template = SKILL_DIR / "assets" / "econ-paper-template.docx"
    if template.stat().st_size < 10_000:
        fail("DOCX template looks too small")
    with zipfile.ZipFile(template) as zf:
        names = set(zf.namelist())
    for member in ["[Content_Types].xml", "word/document.xml", "word/styles.xml"]:
        if member not in names:
            fail(f"DOCX template missing {member}")


def check_python_compile():
    for path in sorted((SKILL_DIR / "scripts").glob("*.py")):
        py_compile.compile(str(path), doraise=True)


def run_command(args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        fail(f"command failed: {' '.join(str(a) for a in args)}")
    return result.stdout


def run_full_smoke_tests():
    with tempfile.TemporaryDirectory(prefix="skill-validation-") as tmp:
        tmpdir = Path(tmp)
        data = tmpdir / "panel.csv"
        data.write_text(
            "firm_id,year,subsidy,dividends,revenue\n"
            "a,2020,0,1.2,10\n"
            "a,2021,1,1.4,12\n"
            "b,2020,0,0.8,8\n"
            "b,2021,1,0.9,9\n",
            encoding="utf-8",
        )
        profile_json = tmpdir / "profile.json"
        roles_json = tmpdir / "roles.json"
        roles_json.write_text(
            json.dumps({"unit": "firm_id", "time": "year", "outcome": "revenue", "treatment": "subsidy"}),
            encoding="utf-8",
        )
        run_command(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "profile_econ_dataset.py"),
                str(data),
                "--out",
                str(tmpdir / "profile.md"),
                "--json-out",
                str(profile_json),
                "--roles-json",
                str(roles_json),
            ]
        )
        profile = json.loads(profile_json.read_text(encoding="utf-8"))
        if profile["analysis_roles"].get("unit") != "firm_id":
            fail("profile smoke test did not preserve the agent-decided unit")
        if profile["analysis_roles"].get("time") != "year":
            fail("profile smoke test did not preserve the agent-decided time key")
        if profile["agent_role_decision_required"]:
            fail("profile smoke test ignored the supplied agent role decision")

        paper_json = tmpdir / "paper.json"
        out_docx = tmpdir / "paper.docx"
        paper_json.write_text(
            json.dumps(
                {
                    "title": "Econometric Smoke Test",
                    "author": "Repository Validation",
                    "abstract": "This generated file validates formulas, tables, and citations.",
                    "sections": [
                        {
                            "heading": "1. Empirical Strategy",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "runs": [
                                        {"text": "The baseline specification follows "},
                                        {"text": "[1]", "superscript": True},
                                        {"text": "."},
                                    ],
                                },
                                {"type": "equation", "text": "y_it=beta_1*x_it+sigma^2_u"},
                                {
                                    "type": "table",
                                    "caption": "Table 1. Smoke regression",
                                    "rows": [["Variable", "(1)"], ["x_it", "0.123"], ["Controls", "Yes"]],
                                    "notes": "Standard errors omitted in this smoke test.",
                                    "source": "Generated validation fixture.",
                                },
                            ],
                        }
                    ],
                    "references": [
                        "Angrist, J. D., and Krueger, A. B. (2001). Instrumental variables and the search for identification."
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        run_command(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "build_paper_docx.py"),
                str(paper_json),
                str(out_docx),
                "--template",
                str(SKILL_DIR / "assets" / "econ-paper-template.docx"),
            ]
        )
        report_text = run_command(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "check_docx_integrity.py"),
                str(out_docx),
                "--json",
            ]
        )
        report = json.loads(report_text)
        if report["omml_count"] < 1:
            fail("DOCX smoke test did not create editable OMML math")
        if report["table_count"] < 1:
            fail("DOCX smoke test did not create a table")
        if report["grid_table_style_count"] != 0:
            fail("DOCX smoke test created grid table styling")
        if report["source_note_count"] < 1:
            fail("DOCX smoke test did not create a source note")
        if report["plain_numeric_citation_markers_preview"]:
            fail("DOCX smoke test found non-superscript numeric citation markers")

        run_command(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(SKILL_DIR / "tests"),
                "-v",
            ]
        )


def main():
    parser = argparse.ArgumentParser(description="Validate repository layout and econometric skill smoke tests.")
    parser.add_argument("--full", action="store_true", help="Run dependency-backed data and DOCX smoke tests.")
    args = parser.parse_args()

    check_required_layout()
    check_skill_metadata()
    check_no_forbidden_text()
    check_docx_template()
    check_python_compile()
    if args.full:
        run_full_smoke_tests()
    print("repository validation passed")


if __name__ == "__main__":
    main()
