"""Count words in RST documents using docutils to strip formatting."""

import re
from pathlib import Path

from docutils import core


RST_DIR = Path("rst")


def _preprocess(text: str) -> str:
    text = re.sub(r'^\.\.\s+include::.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\.\.\s+_\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*:\w+:.*$', '', text, flags=re.MULTILINE)
    return text


def strip_rst(text: str) -> str:
    cleaned = _preprocess(text)
    doctree = core.publish_doctree(
        cleaned,
        settings_overrides={'warning_stream': False, 'line_length_limit': 100_000},
    )
    plain = doctree.astext()
    plain = re.sub(r'\s+', ' ', plain)
    return plain.strip()


def word_count(text: str) -> int:
    plain = strip_rst(text)
    if not plain:
        return 0
    return len(plain.split())


def count_file(path: Path) -> int:
    return word_count(path.read_text(encoding='utf-8'))


def find_rst_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.rst"))


def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Count words in RST files, stripping formatting.")
    parser.add_argument(
        "paths", nargs="*", default=[str(RST_DIR)],
        help="RST files or directories (default: rst/)"
    )
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        files.extend(find_rst_files(Path(p)))

    if not files:
        print("No RST files found.", file=sys.stderr)
        sys.exit(1)

    total = 0
    maxlen = max(len(str(f)) for f in files)
    for f in files:
        wc = count_file(f)
        total += wc
        print(f"{str(f):<{maxlen}}  {wc:>7,}")

    print("-" * (maxlen + 10))
    print(f"{'TOTAL':<{maxlen}}  {total:>7,}")
