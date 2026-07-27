"""Convert RST documents to LaTeX using docutils for both parsing and writing."""

import re
import shutil
from pathlib import Path

from docutils.core import publish_string
from docutils.writers.latex2e import Writer as LaTeXWriter

from intro_to_socialism import _preprocess


RST_DIR = Path("rst")
LATEX_DIR = Path("latex_out")

BODY_RE = re.compile(
    r"\\begin\{document\}\s*\n(.*?)\n\s*\\end\{document\}",
    re.DOTALL,
)

TITLE_BLOCK_RE = re.compile(
    r"\\title\{.*?\}\s*\n\\author\{.*?\}\s*\n\\date\{.*?\}\s*\n\\maketitle\s*\n?",
    re.DOTALL,
)


def _extract_body(latex: str) -> str:
    m = BODY_RE.search(latex)
    if m:
        return m.group(1).strip()
    return latex


def _strip_title_block(latex: str) -> str:
    return TITLE_BLOCK_RE.sub("", latex)


def _demote_headings(latex: str) -> str:
    latex = re.sub(r"^\\section(\s*\{)", r"\\paragraph\1", latex, flags=re.MULTILINE)
    latex = re.sub(
        r"^\\subsection(\s*\{)", r"\\subparagraph\1", latex, flags=re.MULTILINE
    )
    return latex


def convert_rst_to_latex(text: str, fragment: bool = False) -> str:
    preprocessed = _preprocess(text)
    result = publish_string(
        source=preprocessed,
        writer=LaTeXWriter(),
        settings_overrides={
            "warning_stream": False,
            "line_length_limit": 100_000,
            "use_latex_citations": True,
            "legacy_column_widths": False,
        },
    )
    if isinstance(result, bytes):
        result = result.decode("utf-8")
    body = _extract_body(result)
    body = re.sub(r"\n{3,}", "\n\n", body)
    if fragment:
        body = _strip_title_block(body)
        body = _demote_headings(body)
    return body


def convert_file(rst_path: Path, latex_path: Path, fragment: bool = False) -> None:
    rst_text = rst_path.read_text(encoding="utf-8")
    latex_text = convert_rst_to_latex(rst_text, fragment=fragment)
    latex_path.parent.mkdir(parents=True, exist_ok=True)
    latex_path.write_text(latex_text, encoding="utf-8")


def find_rst_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.rst"))


def prepare_main_tex(template_path: Path, output_dir: Path) -> Path:
    """Generate the document-level LaTeX file from the reference template.

    Applies transformations using Python string operations,
    without regular expressions or shell invocation:

    1. Inject required packages and \\date{} after \\documentclass
    2. Replace secnumdepth=0 with secnumdepth=3 plus
       heading-number/-anchor redefinitions
    3. Insert a hyperref bookmark before \\tableofcontents

    Also copies docutils.sty into *output_dir* for the PDF build.
    Returns the path to the generated main ``.tex`` file.
    """
    content = template_path.read_text(encoding="utf-8")

    content = content.replace(
        "\\documentclass[12pt,a4paper]{report}",
        "\\documentclass[12pt,a4paper]{report}\n\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage{url}\n"
        "\\usepackage{hyperref}\n"
        "\\usepackage{xcolor}\n"
        "\\usepackage{docutils}\n"
        "\\date{}",
        1,
    )

    content = content.replace(
        "\\setcounter{secnumdepth}{0}",
        "\\setcounter{secnumdepth}{3}\n"
        "\\renewcommand{\\thesection}{}\n"
        "\\renewcommand{\\theHsection}{\\theHchapter.S\\arabic{section}}\n"
        "\\renewcommand{\\thesubsection}{}\n"
        "\\renewcommand{\\theHsubsection}{\\theHsection.S\\arabic{subsection}}",
    )

    content = content.replace(
        "\\tableofcontents",
        "\\clearpage\n"
        "\\phantomsection\n"
        "\\addcontentsline{toc}{chapter}{Table of Contents}\n"
        "\\tableofcontents",
    )

    main_tex = output_dir / template_path.name
    output_dir.mkdir(parents=True, exist_ok=True)
    main_tex.write_text(content, encoding="utf-8")

    _copy_docutils_sty(output_dir)

    return main_tex


def _copy_docutils_sty(output_dir: Path) -> None:
    """Copy docutils.sty from the installed docutils package."""
    import docutils
    import os

    src = os.path.join(
        os.path.dirname(docutils.__file__),
        "writers",
        "latex2e",
        "docutils.sty",
    )
    dst = output_dir / "docutils.sty"
    shutil.copy(src, dst)


def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Convert RST files to LaTeX using docutils.")
    parser.add_argument(
        "paths", nargs="*", default=[str(RST_DIR)],
        help="RST files or directories (default: rst/)"
    )
    parser.add_argument(
        "-o", "--output-dir", default=str(LATEX_DIR),
        help=f"Output directory for LaTeX files (default: {LATEX_DIR})"
    )
    parser.add_argument(
        "--fragment", action="store_true",
        help="Produce includable fragments: strip the title block and demote headings"
    )
    parser.add_argument(
        "--main-template", type=Path,
        help="Path to the reference LaTeX template from which to generate the document-level .tex file"
    )
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        files.extend(find_rst_files(Path(p)))

    if not files:
        print("No RST files found.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for rst_file in files:
        rel = rst_file.relative_to(RST_DIR) if RST_DIR in rst_file.parents else rst_file.name
        latex_file = out_dir / rel.with_suffix(".tex")
        convert_file(rst_file, latex_file, fragment=args.fragment)
        print(f"  {rst_file} -> {latex_file}")

    if args.fragment and args.main_template:
        main_tex = prepare_main_tex(args.main_template.resolve(), out_dir)
        print(f"  template  -> {main_tex}")

    print(f"Done. {len(files)} files written to {out_dir.resolve()}/")


if __name__ == "__main__":
    main()
