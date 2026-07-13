import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def renderer_candidates_from_root(root):
    root = Path(root).expanduser()
    candidates = [
        root / "render_docx.py",
        root / "documents/render_docx.py",
        root / "skills/documents/render_docx.py",
    ]
    candidates.extend(sorted(root.glob("*/skills/documents/render_docx.py"), reverse=True))
    candidates.extend(sorted(root.glob("documents/*/skills/documents/render_docx.py"), reverse=True))
    candidates.extend(sorted(root.glob("*/documents/*/skills/documents/render_docx.py"), reverse=True))
    return candidates


def bundled_renderer_candidates():
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    roots = [
        codex_home / "plugins/cache/openai-primary-runtime",
        codex_home / "plugins/cache/openai-bundled",
        codex_home / "skills",
    ]
    candidates = []
    for root in roots:
        if root.exists():
            candidates.extend(renderer_candidates_from_root(root))
    return candidates


def bundled_dependency_roots():
    roots = []
    explicit = os.environ.get("WORKSPACE_DEPENDENCIES_ROOT")
    if explicit:
        roots.append(Path(explicit).expanduser())
    runtime_cache = Path.home() / ".cache/codex-runtimes"
    if runtime_cache.exists():
        roots.extend(sorted(runtime_cache.glob("*/dependencies"), reverse=True))
    return [root for root in roots if root.exists()]


def find_renderer():
    for env_name in ["DOCX_RENDER_SCRIPT", "DOCUMENTS_RENDER_SCRIPT"]:
        value = os.environ.get(env_name)
        if value:
            path = Path(value).expanduser()
            if path.exists():
                return path

    for env_name in ["DOCUMENTS_SKILL_ROOT", "DOCUMENT_RENDERER_SEARCH_ROOTS"]:
        value = os.environ.get(env_name)
        if not value:
            continue
        for part in value.split(os.pathsep):
            if not part:
                continue
            for path in renderer_candidates_from_root(part):
                if path.exists():
                    return path

    for path in bundled_renderer_candidates():
        if path.exists():
            return path

    for command in ["render_docx.py", "render_docx"]:
        value = shutil.which(command)
        if value:
            return Path(value)

    return None


def choose_python():
    candidates = [
        os.environ.get("WORKSPACE_PYTHON"),
        os.environ.get("PYTHON"),
    ]
    for root in bundled_dependency_roots():
        candidates.extend([root / "python/bin/python", root / "python/bin/python3"])
    candidates.extend([sys.executable, shutil.which("python3")])
    for value in candidates:
        if not value:
            continue
        path = Path(value).expanduser()
        if path.exists():
            return str(path)
    return sys.executable


def render_env():
    env = os.environ.copy()
    bin_value = os.environ.get("WORKSPACE_BIN") or os.environ.get("DOCUMENT_RENDERER_BIN")
    if not bin_value:
        for root in bundled_dependency_roots():
            candidate = root / "bin/override"
            if candidate.exists():
                bin_value = str(candidate)
                break
    if bin_value and Path(bin_value).expanduser().exists():
        current = env.get("PATH", "")
        env["PATH"] = str(Path(bin_value).expanduser()) + (os.pathsep + current if current else "")
    return env


def clear_stale_outputs(output_dir, input_path, emit_pdf=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    removed = []
    for path in output_dir.glob("page-*.png"):
        path.unlink()
        removed.append(path)
    if emit_pdf:
        pdf_path = output_dir / f"{input_path.stem}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
            removed.append(pdf_path)
    return removed


def main():
    parser = argparse.ArgumentParser(description="Render a DOCX for visual QA using the bundled document renderer.")
    parser.add_argument("docx")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--emit-pdf", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.docx).expanduser()
    if not input_path.is_file():
        raise SystemExit(f"Error: input DOCX does not exist or is not a file: {input_path}")
    output_dir = Path(args.output_dir).expanduser()
    if output_dir.exists() and not output_dir.is_dir():
        raise SystemExit(f"Error: output path exists and is not a directory: {output_dir}")

    renderer = find_renderer()
    if renderer is None:
        raise SystemExit(
            "Error: visual QA was not run because documents/render_docx.py could not be found. "
            "Load the bundled workspace dependencies or set DOCX_RENDER_SCRIPT."
        )

    clear_stale_outputs(output_dir, input_path, emit_pdf=args.emit_pdf)

    cmd = [choose_python(), str(renderer), str(input_path), "--output_dir", str(output_dir)]
    if args.emit_pdf:
        cmd.append("--emit_pdf")
    try:
        subprocess.check_call(cmd, env=render_env(), timeout=300)
    except subprocess.TimeoutExpired:
        raise SystemExit("Error: rendering process timed out after 300 seconds.")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Error: document renderer failed with exit code {exc.returncode}.")
    pngs = sorted(output_dir.glob("page-*.png"))
    if not pngs:
        raise SystemExit("render produced no page PNGs")
    print(f"rendered_pages: {len(pngs)}")
    for p in pngs:
        print(p)


if __name__ == "__main__":
    main()
