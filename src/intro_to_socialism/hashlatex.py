"""Produce a lowercased, whitespace-normalized text from LaTeX and its SHA-512 hash.

This provides a content-fingerprint that remains stable across formatting
changes, so long as the actual article text is unchanged.
"""

import hashlib
from pathlib import Path

from intro_to_socialism.latexwc import strip_latex


LATEX_DIR = Path("latex")


def normalize(text: str) -> str:
    stripped = strip_latex(text)
    return stripped.lower()


def content_hash(text: str) -> str:
    return hashlib.sha512(normalize(text).encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    return content_hash(path.read_text(encoding="utf-8"))


def find_tex_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.tex"))


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Lowercase normalized LaTeX content and its SHA-512 hash."
    )
    parser.add_argument(
        "paths", nargs="*", default=[str(LATEX_DIR)],
        help="LaTeX files or directories (default: latex/)"
    )
    parser.add_argument(
        "--hash-only", action="store_true",
        help="Print only the final combined hash"
    )
    parser.add_argument(
        "--dump", metavar="PATH",
        help="Write normalized text to PATH for inspection"
    )
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        files.extend(find_tex_files(Path(p)))

    if not files:
        import sys
        print("No .tex files found.", file=sys.stderr)
        sys.exit(1)

    combined = hashlib.sha512()

    for f in files:
        norm = normalize(f.read_text(encoding="utf-8"))
        fhash = hashlib.sha512(norm.encode("utf-8")).hexdigest()
        combined.update(norm.encode("utf-8"))

        if not args.hash_only:
            print(f"{fhash}  {f}")

    if args.dump:
        all_text = ""
        for f in files:
            all_text += normalize(f.read_text(encoding="utf-8"))
        Path(args.dump).write_text(all_text, encoding="utf-8")
        print(f"Wrote normalized text to {args.dump}", file=sys.stderr)

    print(combined.hexdigest())


if __name__ == "__main__":
    main()
