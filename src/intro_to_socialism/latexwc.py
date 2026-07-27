"""Count words in LaTeX documents using TexSoup to strip formatting."""

import re
from pathlib import Path

from TexSoup import TexSoup

LATEX_DIR = Path("latex")


def strip_latex(text: str) -> str:
    soup = TexSoup(text, tolerance=1)
    return re.sub(r'\s+', ' ', ' '.join(soup.text)).strip()


def word_count(text: str) -> int:
    plain = strip_latex(text)
    if not plain:
        return 0
    return len(plain.split())


def count_file(path: Path) -> int:
    return word_count(path.read_text(encoding='utf-8'))


def find_tex_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.tex"))


def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Count words in LaTeX files, stripping formatting.")
    parser.add_argument(
        "paths", nargs="*", default=[str(LATEX_DIR)],
        help="LaTeX files or directories (default: latex/)"
    )
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        files.extend(find_tex_files(Path(p)))

    if not files:
        print("No .tex files found.", file=sys.stderr)
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
