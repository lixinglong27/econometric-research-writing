import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def read_xml(zf, name):
    try:
        return zf.read(name)
    except KeyError:
        return b""


def border_is_active(element):
    if element is None:
        return False
    value = element.attrib.get(f"{{{NS['w']}}}val", "single").lower()
    return value not in {"nil", "none", "0"}


def active_borders(parent, path):
    borders = parent.find(path, NS)
    if borders is None:
        return set()
    return {
        edge
        for edge in ["top", "bottom", "left", "right", "insideH", "insideV"]
        if border_is_active(borders.find(f"./w:{edge}", NS))
    }


def nonblack_color_descriptor(color):
    """Return color metadata when a style/direct override can render non-black."""

    if color is None:
        return None
    value = color.attrib.get(f"{{{NS['w']}}}val", "")
    theme = color.attrib.get(f"{{{NS['w']}}}themeColor", "")
    value_is_nonblack = bool(value and value.upper() not in {"000000", "AUTO"})
    theme_is_nonblack = bool(
        theme and theme.lower() not in {"dark1", "text1", "none"}
    )
    if not value_is_nonblack and not theme_is_nonblack:
        return None
    return {"color": value, "theme_color": theme}


def inspect_table_borders(table):
    table_borders = active_borders(table, "./w:tblPr/w:tblBorders")
    row_borders = []
    for row in table.findall("./w:tr", NS):
        cells = row.findall("./w:tc", NS)
        row_borders.append([
            active_borders(cell, "./w:tcPr/w:tcBorders") for cell in cells
        ])

    def every_cell(row_index, edge):
        if row_index < 0 or row_index >= len(row_borders) or not row_borders[row_index]:
            return False
        return all(edge in borders for borders in row_borders[row_index])

    first_top = "top" in table_borders or every_cell(0, "top")
    last_bottom = "bottom" in table_borders or every_cell(len(row_borders) - 1, "bottom")
    header_separator_rows = [
        index for index in range(max(0, len(row_borders) - 1))
        if every_cell(index, "bottom")
    ]
    if len(row_borders) == 1 and every_cell(0, "bottom"):
        header_separator_rows = [0]

    vertical = bool(table_borders & {"left", "right", "insideV"}) or any(
        borders & {"left", "right", "insideV"}
        for row in row_borders for borders in row
    )
    inside_horizontal = "insideH" in table_borders or any(
        "insideH" in borders for row in row_borders for borders in row
    )
    horizontal = bool(table_borders & {"top", "bottom", "insideH"}) or any(
        borders & {"top", "bottom", "insideH"}
        for row in row_borders for borders in row
    )
    three_line = bool(
        first_top
        and last_bottom
        and header_separator_rows
        and not vertical
        and not inside_horizontal
    )
    return {
        "row_count": len(row_borders),
        "first_row_top_rule": first_top,
        "last_row_bottom_rule": last_bottom,
        "header_separator_rows": header_separator_rows,
        "has_vertical_borders": vertical,
        "has_inside_horizontal_borders": inside_horizontal,
        "has_explicit_horizontal_borders": horizontal,
        "three_line": three_line,
        "explicit_grid": bool(vertical and horizontal),
    }


def inspect_docx(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"DOCX file not found: {path}")
    with zipfile.ZipFile(path) as zf:
        document_xml = read_xml(zf, "word/document.xml")
        styles_xml = read_xml(zf, "word/styles.xml")
        root = ET.fromstring(document_xml)
        styles = ET.fromstring(styles_xml) if styles_xml else None
        media = [n for n in zf.namelist() if n.startswith("word/media/")]

    headings = []
    nonblack_heading_direct_formatting = []
    for p in root.findall(".//w:p", NS):
        pstyle = p.find("./w:pPr/w:pStyle", NS)
        if pstyle is not None:
            val = pstyle.attrib.get(f"{{{NS['w']}}}val", "")
            if val.lower().startswith("heading"):
                text = "".join(t.text or "" for t in p.findall(".//w:t", NS))
                headings.append({"style": val, "text": text[:120]})
                paragraph_color = nonblack_color_descriptor(
                    p.find("./w:pPr/w:rPr/w:color", NS)
                )
                if paragraph_color:
                    nonblack_heading_direct_formatting.append(
                        {
                            "style": val,
                            "text": text[:120],
                            "scope": "paragraph",
                            **paragraph_color,
                        }
                    )
                for run in p.findall(".//w:r", NS):
                    run_color = nonblack_color_descriptor(
                        run.find("./w:rPr/w:color", NS)
                    )
                    if run_color:
                        run_text = "".join(
                            node.text or "" for node in run.findall(".//w:t", NS)
                        )
                        nonblack_heading_direct_formatting.append(
                            {
                                "style": val,
                                "text": (run_text or text)[:120],
                                "scope": "run",
                                **run_color,
                            }
                        )

    tables = root.findall(".//w:tbl", NS)
    grid_table_count = 0
    table_border_summaries = []
    for tbl in tables:
        tbl_style = tbl.find("./w:tblPr/w:tblStyle", NS)
        val = tbl_style.attrib.get(f"{{{NS['w']}}}val", "") if tbl_style is not None else ""
        style_is_grid = val.lower() in {"tablegrid", "gridtable"}
        if style_is_grid:
            grid_table_count += 1
        summary = inspect_table_borders(tbl)
        summary["style"] = val
        summary["style_is_grid"] = style_is_grid
        table_border_summaries.append(summary)

    superscript_run_count = 0
    for run in root.findall(".//w:r", NS):
        vert_align = run.find("./w:rPr/w:vertAlign", NS)
        if vert_align is None:
            continue
        if vert_align.attrib.get(f"{{{NS['w']}}}val", "").lower() == "superscript":
            superscript_run_count += 1

    plain_numeric_citation_markers = []
    table_caption_count = 0
    figure_caption_count = 0
    source_note_count = 0
    for p in root.findall(".//w:p", NS):
        chars = []
        superscript_flags = []
        for run in p.findall("./w:r", NS):
            vert_align = run.find("./w:rPr/w:vertAlign", NS)
            is_superscript = (
                vert_align is not None
                and vert_align.attrib.get(f"{{{NS['w']}}}val", "").lower() == "superscript"
            )
            run_text = "".join(t.text or "" for t in run.findall(".//w:t", NS))
            chars.append(run_text)
            superscript_flags.extend([is_superscript] * len(run_text))
        text = "".join(chars).strip()
        if not text:
            continue
        leading_space = len("".join(chars)) - len("".join(chars).lstrip())
        for match in re.finditer(r"\[\d{1,3}\]", text):
            start = leading_space + match.start()
            end = leading_space + match.end()
            if not superscript_flags[start:end] or not all(superscript_flags[start:end]):
                plain_numeric_citation_markers.append(text[:160])
                break
        if text.lower().startswith("table "):
            table_caption_count += 1
        if text.lower().startswith("figure "):
            figure_caption_count += 1
        if text.lower().startswith("source:"):
            source_note_count += 1

    blue_heading_styles = []
    core_style_audit = []
    title_style_has_paragraph_border = False
    if styles is not None:
        for style in styles.findall(".//w:style", NS):
            style_id = style.attrib.get(f"{{{NS['w']}}}styleId", "")
            if style_id.lower().startswith("heading"):
                color = style.find(".//w:color", NS)
                descriptor = nonblack_color_descriptor(color)
                if descriptor:
                    blue_heading_styles.append({"style": style_id, **descriptor})
            if style_id.lower() in {"title", "subtitle", "caption"}:
                color = style.find("./w:rPr/w:color", NS)
                color_value = (
                    color.attrib.get(f"{{{NS['w']}}}val", "") if color is not None else ""
                )
                borders = style.find("./w:pPr/w:pBdr", NS)
                has_border_element = borders is not None
                active_border_names = active_borders(style, "./w:pPr/w:pBdr")
                if style_id.lower() == "title" and has_border_element:
                    title_style_has_paragraph_border = True
                core_style_audit.append({
                    "style": style_id,
                    "color": color_value,
                    "is_explicit_black": color_value.upper() == "000000",
                    "has_paragraph_border_element": has_border_element,
                    "active_paragraph_borders": sorted(active_border_names),
                })

    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "omml_count": len(root.findall(".//m:oMath", NS)),
        "table_count": len(tables),
        "grid_table_style_count": grid_table_count,
        "grid_table_border_count": sum(item["explicit_grid"] for item in table_border_summaries),
        "grid_table_count": sum(
            item["style_is_grid"] or item["explicit_grid"] for item in table_border_summaries
        ),
        "three_line_table_count": sum(item["three_line"] for item in table_border_summaries),
        "vertical_border_table_count": sum(
            item["has_vertical_borders"] for item in table_border_summaries
        ),
        "table_border_summaries": table_border_summaries,
        "media_count": len(media),
        "table_caption_count": table_caption_count,
        "figure_caption_count": figure_caption_count,
        "source_note_count": source_note_count,
        "superscript_run_count": superscript_run_count,
        "plain_numeric_citation_markers_preview": plain_numeric_citation_markers[:12],
        "heading_count": len(headings),
        "headings_preview": headings[:12],
        "nonblack_heading_styles": blue_heading_styles,
        "nonblack_heading_direct_formatting": nonblack_heading_direct_formatting[:24],
        "core_style_audit": core_style_audit,
        "missing_core_styles": sorted(
            {"title", "subtitle", "caption"}
            - {item["style"].lower() for item in core_style_audit}
        ),
        "nonblack_core_style_count": sum(
            not item["is_explicit_black"] for item in core_style_audit
        ),
        "title_style_has_paragraph_border": title_style_has_paragraph_border,
    }


def assertion_failures(
    report,
    *,
    min_omml=0,
    min_tables=0,
    min_media=0,
    min_headings=0,
    min_superscript_runs=0,
    require_three_line_tables=False,
    forbid_grid_tables=False,
    fail_on_plain_citations=False,
    fail_on_nonblack_headings=False,
    require_clean_core_styles=False,
):
    checks = [
        ("omml_count", min_omml),
        ("table_count", min_tables),
        ("media_count", min_media),
        ("heading_count", min_headings),
        ("superscript_run_count", min_superscript_runs),
    ]
    failures = []
    for key, minimum in checks:
        if report.get(key, 0) < minimum:
            failures.append(f"{key}={report.get(key, 0)} is below required minimum {minimum}")
    if require_three_line_tables and report.get("table_count", 0) != report.get("three_line_table_count", 0):
        failures.append(
            "not every table has detected top, header-bottom, and bottom rules without vertical borders"
        )
    if forbid_grid_tables and report.get("grid_table_count", 0):
        failures.append(f"grid_table_count={report['grid_table_count']} but grid tables are forbidden")
    if fail_on_plain_citations and report.get("plain_numeric_citation_markers_preview"):
        failures.append("plain numeric citation markers were detected")
    if fail_on_nonblack_headings:
        if report.get("nonblack_heading_styles"):
            failures.append("non-black heading styles were detected")
        if report.get("nonblack_heading_direct_formatting"):
            failures.append("non-black direct formatting was detected in heading paragraphs")
    if require_clean_core_styles:
        if report.get("missing_core_styles"):
            failures.append(
                "missing core styles: " + ", ".join(report["missing_core_styles"])
            )
        if report.get("nonblack_core_style_count", 0):
            failures.append("Title, Subtitle, or Caption is not explicitly black")
        if report.get("title_style_has_paragraph_border"):
            failures.append("Title style contains a paragraph-border element")
    return failures


def main():
    parser = argparse.ArgumentParser(description="Inspect DOCX formulas, tables, media, and heading styles.")
    parser.add_argument("docx")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-omml", action="store_true", help="Require at least one OMML equation.")
    parser.add_argument("--require-tables", action="store_true", help="Require at least one table.")
    parser.add_argument("--require-media", action="store_true", help="Require at least one embedded media file.")
    parser.add_argument("--require-headings", action="store_true", help="Require at least one heading paragraph.")
    parser.add_argument("--require-superscript", action="store_true", help="Require at least one superscript run.")
    parser.add_argument("--min-omml", type=int, default=0)
    parser.add_argument("--min-tables", type=int, default=0)
    parser.add_argument("--min-media", type=int, default=0)
    parser.add_argument("--min-headings", type=int, default=0)
    parser.add_argument("--min-superscript-runs", type=int, default=0)
    parser.add_argument("--require-three-line-tables", action="store_true")
    parser.add_argument("--forbid-grid-tables", action="store_true")
    parser.add_argument("--fail-on-plain-citations", action="store_true")
    parser.add_argument("--fail-on-nonblack-headings", action="store_true")
    parser.add_argument(
        "--require-clean-core-styles",
        action="store_true",
        help="Require Title/Subtitle/Caption to be explicitly black and Title to contain no paragraph border.",
    )
    args = parser.parse_args()

    try:
        report = inspect_docx(args.docx)
    except (FileNotFoundError, zipfile.BadZipFile, ET.ParseError) as exc:
        parser.error(str(exc))
    failures = assertion_failures(
        report,
        min_omml=max(args.min_omml, int(args.require_omml)),
        min_tables=max(args.min_tables, int(args.require_tables)),
        min_media=max(args.min_media, int(args.require_media)),
        min_headings=max(args.min_headings, int(args.require_headings)),
        min_superscript_runs=max(args.min_superscript_runs, int(args.require_superscript)),
        require_three_line_tables=args.require_three_line_tables,
        forbid_grid_tables=args.forbid_grid_tables,
        fail_on_plain_citations=args.fail_on_plain_citations,
        fail_on_nonblack_headings=args.fail_on_nonblack_headings,
        require_clean_core_styles=args.require_clean_core_styles,
    )
    report["assertion_failures"] = failures
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
