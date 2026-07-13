import argparse
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path


CROSSREF_WORKS = "https://api.crossref.org/works"


def normalize_text(value):
    """Normalize Unicode text without discarding non-Latin scripts."""
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = "".join(char if char.isalnum() else " " for char in value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value):
    return normalize_text(value)


def title_similarity(a, b):
    a_norm = normalize_title(a)
    b_norm = normalize_title(b)
    if not a_norm or not b_norm:
        return 0.0
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


def author_family_names(value):
    """Return normalized family-name candidates from common author formats."""
    if not value:
        return set()
    if isinstance(value, (str, dict)):
        value = [value]
    families = set()
    for author in value:
        if isinstance(author, dict):
            name = author.get("family") or author.get("name") or ""
        else:
            name = str(author)
        normalized = normalize_text(name)
        if not normalized:
            continue
        # Crossref returns family names separately. For free-form input, the
        # final token is the least surprising comparison key.
        families.add(normalized.split()[-1])
    return families


def author_similarity(input_authors, matched_authors):
    left = author_family_names(input_authors)
    right = author_family_names(matched_authors)
    if not left or not right:
        return None
    return len(left & right) / len(left | right)


def normalized_year(value):
    match = re.search(r"\d{4}", str(value or ""))
    return int(match.group(0)) if match else None


def metadata_match(ref, matched):
    """Score a candidate across every supplied identity field."""
    title_score = title_similarity(ref.get("title"), matched.get("title"))
    input_authors = ref.get("authors") or ref.get("author")
    authors_score = author_similarity(input_authors, matched.get("authors"))
    input_year = normalized_year(ref.get("year"))
    matched_year = normalized_year(matched.get("year"))
    year_score = None if input_year is None or matched_year is None else float(input_year == matched_year)
    input_container = ref.get("container_title") or ref.get("journal") or ref.get("venue")
    matched_container = matched.get("container_title")
    container_score = (
        title_similarity(input_container, matched_container)
        if input_container and matched_container
        else None
    )

    field_scores = {
        "title": title_score,
        "authors": authors_score,
        "year": year_score,
        "container_title": container_score,
    }
    weights = {"title": 0.65, "authors": 0.20, "year": 0.10, "container_title": 0.05}
    available = [(weights[name], score) for name, score in field_scores.items() if score is not None]
    composite = sum(weight * score for weight, score in available) / sum(weight for weight, _ in available)

    corroborating_matches = []
    if authors_score is not None and authors_score > 0:
        corroborating_matches.append("authors")
    if year_score == 1.0:
        corroborating_matches.append("year")
    if container_score is not None and container_score >= 0.75:
        corroborating_matches.append("container_title")

    mismatches = []
    if ref.get("title") and title_score < 0.80:
        mismatches.append("title")
    if authors_score is not None and authors_score == 0:
        mismatches.append("authors")
    if year_score == 0.0:
        mismatches.append("year")

    return {
        "composite": composite,
        "field_scores": field_scores,
        "corroborating_matches": corroborating_matches,
        "mismatches": mismatches,
    }


def request_json(url, timeout=20, mailto="unknown@example.com"):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": f"econometric-research-writing-skill/1.0 (mailto:{mailto})",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def crossref_by_doi(doi, mailto="unknown@example.com"):
    url = f"{CROSSREF_WORKS}/{urllib.parse.quote(doi.strip())}"
    return request_json(url, mailto=mailto).get("message", {})


def crossref_by_title(title, rows=3, mailto="unknown@example.com"):
    params = urllib.parse.urlencode({"query.title": title, "rows": rows})
    url = f"{CROSSREF_WORKS}?{params}"
    return request_json(url, mailto=mailto).get("message", {}).get("items", [])


def authors_from_crossref(item):
    authors = []
    for author in item.get("author", []):
        family = author.get("family")
        given = author.get("given")
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
    return authors


def year_from_crossref(item):
    for key in ["published-print", "published-online", "published", "issued"]:
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
    return None


def summarize_crossref_item(item):
    titles = item.get("title") or []
    return {
        "title": titles[0] if titles else "",
        "authors": authors_from_crossref(item),
        "year": year_from_crossref(item),
        "container_title": (item.get("container-title") or [""])[0],
        "doi": item.get("DOI", ""),
        "url": item.get("URL", ""),
        "type": item.get("type", ""),
    }


def verify_reference(ref, sleep_seconds=0.25, mailto="unknown@example.com"):
    title = ref.get("title", "")
    doi = ref.get("doi") or ref.get("DOI")
    result = {
        "input": ref,
        "status": "not_checked",
        "match_score": None,
        "field_scores": None,
        "matched": None,
        "warning": None,
    }

    try:
        if doi:
            item = crossref_by_doi(doi, mailto=mailto)
            matched = summarize_crossref_item(item)
            details = metadata_match(ref, matched)
            result.update({
                "status": "verified_by_doi",
                "match_score": details["composite"],
                "field_scores": details["field_scores"],
                "matched": matched,
            })
            if details["mismatches"]:
                result["status"] = "metadata_mismatch"
                result["warning"] = (
                    "DOI resolved, but supplied metadata disagrees on: "
                    + ", ".join(details["mismatches"])
                    + "."
                )
            time.sleep(sleep_seconds)
            return result

        if title:
            items = crossref_by_title(title, rows=5, mailto=mailto)
            candidates = [summarize_crossref_item(item) for item in items]
            scored = [(metadata_match(ref, item), item) for item in candidates]
            scored.sort(
                key=lambda pair: (pair[0]["composite"], pair[0]["field_scores"]["title"]),
                reverse=True,
            )
            if scored:
                details, matched = scored[0]
                title_score = details["field_scores"]["title"]
                result.update({
                    "match_score": details["composite"],
                    "field_scores": details["field_scores"],
                    "matched": matched,
                })
                if details["mismatches"]:
                    result["status"] = "metadata_mismatch"
                    result["warning"] = (
                        "Best Crossref candidate disagrees on: "
                        + ", ".join(details["mismatches"])
                        + "."
                    )
                elif title_score >= 0.90 and details["corroborating_matches"]:
                    result["status"] = "verified_by_metadata"
                elif title_score >= 0.85:
                    result["status"] = "candidate_match"
                    result["warning"] = (
                        "Title match found, but no supplied author/year/venue field independently corroborates it."
                    )
                else:
                    result["status"] = "needs_manual_review"
                    result["warning"] = "No high-confidence Crossref metadata match found."
            else:
                result.update({"status": "needs_manual_review", "match_score": 0.0})
                result["warning"] = "No high-confidence Crossref title match found."
            time.sleep(sleep_seconds)
            return result

        result["status"] = "insufficient_metadata"
        result["warning"] = "Reference has neither DOI nor title."
        return result
    except Exception as exc:
        result["status"] = "verification_error"
        result["warning"] = str(exc)
        return result


def load_references(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("references", [])
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list or an object with a 'references' list.")
    return data


def write_markdown(results, out_path):
    lines = [
        "# Reference Verification Report",
        "",
        "| # | Status | Input title | Matched title | DOI | Warning |",
        "|---:|---|---|---|---|---|",
    ]
    for index, item in enumerate(results, start=1):
        ref = item.get("input", {})
        matched = item.get("matched") or {}
        lines.append(
            "| {idx} | {status} | {input_title} | {matched_title} | {doi} | {warning} |".format(
                idx=index,
                status=item.get("status", ""),
                input_title=(ref.get("title") or "").replace("|", "\\|"),
                matched_title=(matched.get("title") or "").replace("|", "\\|"),
                doi=(matched.get("doi") or ref.get("doi") or ref.get("DOI") or "").replace("|", "\\|"),
                warning=(item.get("warning") or "").replace("|", "\\|"),
            )
        )
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def enriched_reference(result):
    ref = dict(result.get("input", {}))
    matched = result.get("matched") or {}
    status = result.get("status")
    if matched and status in {"verified_by_doi", "verified_by_metadata"}:
        return {
            "title": matched.get("title") or ref.get("title"),
            "authors": matched.get("authors") or ref.get("authors", []),
            "year": matched.get("year") or ref.get("year"),
            "container_title": matched.get("container_title") or ref.get("container_title") or ref.get("journal"),
            "doi": matched.get("doi") or ref.get("doi") or ref.get("DOI"),
            "url": matched.get("url") or ref.get("url"),
            "type": matched.get("type") or ref.get("type"),
            "verification_status": status,
            "match_score": result.get("match_score"),
            "field_scores": result.get("field_scores"),
        }

    ref["verification_status"] = status
    ref["match_score"] = result.get("match_score")
    ref["field_scores"] = result.get("field_scores")
    if result.get("warning"):
        ref["warning"] = result["warning"]
    return ref


def main():
    parser = argparse.ArgumentParser(description="Verify reference metadata against Crossref by DOI or title.")
    parser.add_argument("references_json", help="JSON list of references or {'references': [...]} object.")
    parser.add_argument("--out-md", help="Write a Markdown verification report.")
    parser.add_argument("--out-json", help="Write raw JSON verification results.")
    parser.add_argument("--out-enriched-json", help="Write normalized reference metadata for verified items.")
    parser.add_argument("--mailto", help="Contact email to include in the Crossref API User-Agent for polite pool access.")
    args = parser.parse_args()

    mailto = args.mailto or os.environ.get("CROSSREF_MAILTO") or "unknown@example.com"
    refs = load_references(args.references_json)
    results = [verify_reference(ref, mailto=mailto) for ref in refs]

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.out_md:
        write_markdown(results, args.out_md)
    if args.out_enriched_json:
        enriched = [enriched_reference(item) for item in results]
        Path(args.out_enriched_json).write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.out_json and not args.out_md and not args.out_enriched_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    bad_statuses = {
        "candidate_match",
        "metadata_mismatch",
        "needs_manual_review",
        "insufficient_metadata",
        "verification_error",
    }
    if any(item.get("status") in bad_statuses for item in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
