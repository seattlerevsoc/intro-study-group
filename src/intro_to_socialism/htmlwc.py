"""Count words in HTML/XHTML documents using BeautifulSoup to strip formatting."""

import re
from pathlib import Path

from bs4 import BeautifulSoup


EPUB_DIR = Path("epub")


def strip_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return re.sub(r'\s+', ' ', soup.get_text()).strip()


def word_count(text: str) -> int:
    plain = strip_html(text)
    if not plain:
        return 0
    return len(plain.split())


def count_file(path: Path) -> int:
    return word_count(path.read_text(encoding="utf-8"))


def find_html_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    files: list[Path] = []
    files.extend(sorted(path.rglob("*.xhtml")))
    files.extend(sorted(path.rglob("*.html")))
    return sorted(files)


def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Count words in HTML/XHTML files, stripping formatting.")
    parser.add_argument(
        "paths", nargs="*", default=[str(EPUB_DIR)],
        help="HTML/XHTML files or directories (default: epub/)"
    )
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        files.extend(find_html_files(Path(p)))

    if not files:
        print("No .html or .xhtml files found.", file=sys.stderr)
        sys.exit(1)

    total = 0
    maxlen = max(len(str(f)) for f in files)
    for f in files:
        wc = count_file(f)
        total += wc
        print(f"{str(f):<{maxlen}}  {wc:>7,}")

    print("-" * (maxlen + 10))
    print(f"{'TOTAL':<{maxlen}}  {total:>7,}")


if __name__ == "__main__":
    main()
