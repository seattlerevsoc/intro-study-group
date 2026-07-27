"""Convert RST documents to XHTML using docutils for both parsing and writing."""

import re
from pathlib import Path

from docutils.core import publish_string
from docutils.writers.html5_polyglot import Writer as XHTMLWriter

from intro_to_socialism import _preprocess


RST_DIR = Path("rst")
XHTML_DIR = Path("xhtml_out")

MAIN_RE = re.compile(r"<main\b[^>]*>.*?</main>", re.DOTALL)


def _extract_main(xhtml: str) -> str:
    m = MAIN_RE.search(xhtml)
    if m:
        return m.group(0)
    return xhtml


def convert_rst_to_xhtml(text: str) -> str:
    preprocessed = _preprocess(text)
    result = publish_string(
        source=preprocessed,
        writer=XHTMLWriter(),
        settings_overrides={
            "warning_stream": False,
            "line_length_limit": 100_000,
        },
    )
    if isinstance(result, bytes):
        result = result.decode("utf-8")
    body = _extract_main(result)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body


def convert_file(rst_path: Path, xhtml_path: Path) -> None:
    rst_text = rst_path.read_text(encoding="utf-8")
    xhtml_text = convert_rst_to_xhtml(rst_text)
    xhtml_path.parent.mkdir(parents=True, exist_ok=True)
    xhtml_path.write_text(xhtml_text, encoding="utf-8")


def find_rst_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.rst"))


def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Convert RST files to XHTML using docutils.")
    parser.add_argument(
        "paths", nargs="*", default=[str(RST_DIR)],
        help="RST files or directories (default: rst/)"
    )
    parser.add_argument(
        "-o", "--output-dir", default=str(XHTML_DIR),
        help=f"Output directory for XHTML files (default: {XHTML_DIR})"
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
        xhtml_file = out_dir / rel.with_suffix(".xhtml")
        convert_file(rst_file, xhtml_file)
        print(f"  {rst_file} -> {xhtml_file}")

    print(f"Done. {len(files)} files written to {out_dir.resolve()}/")


if __name__ == "__main__":
    main()
