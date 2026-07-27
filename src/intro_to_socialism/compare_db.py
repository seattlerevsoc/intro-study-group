"""Compare original web articles (in articles.db) against the book's RST sources.

Uses word‑set (Jaccard) similarity to detect content changes
independently of formatting and structural differences.

For articles below 95% Jaccard, also provides paragraph‑by‑paragraph diffs.
"""

import difflib
import re
import sqlite3
from pathlib import Path

from docutils import nodes
from docutils.core import publish_doctree

DB_PATH = Path("articles.db")
RST_ARTICLES_DIR = Path("rst/articles")
OUTPUT_PATH = Path("comparison_report.html")

WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _load_db_text(conn: sqlite3.Connection, name: str) -> str:
    rows = conn.execute(
        "SELECT text FROM paragraphs WHERE article_id IN "
        "(SELECT id FROM articles WHERE name = ?) "
        "ORDER BY paragraph_num",
        (name,),
    ).fetchall()
    return " ".join(r[0] for r in rows)


def _load_db_paragraphs(conn: sqlite3.Connection, name: str) -> list[str]:
    rows = conn.execute(
        "SELECT text FROM paragraphs WHERE article_id IN "
        "(SELECT id FROM articles WHERE name = ?) "
        "ORDER BY paragraph_num",
        (name,),
    ).fetchall()
    return [r[0] for r in rows]


def _load_rst_text(name: str) -> str:
    from intro_to_socialism import strip_rst

    rst_path = RST_ARTICLES_DIR / f"{name}.rst"
    if not rst_path.exists():
        return ""
    return strip_rst(rst_path.read_text(encoding="utf-8"))


def _load_rst_paragraphs(name: str) -> list[str]:
    from intro_to_socialism import _preprocess

    rst_path = RST_ARTICLES_DIR / f"{name}.rst"
    if not rst_path.exists():
        return []
    cleaned = _preprocess(rst_path.read_text(encoding="utf-8"))
    doctree = publish_doctree(
        cleaned,
        settings_overrides={
            "warning_stream": False,
            "line_length_limit": 100_000,
        },
    )

    def _walk(node: nodes.Node) -> list[str]:
        results: list[str] = []
        if isinstance(node, nodes.paragraph):
            text = node.astext().strip()
            if text and len(text.split()) > 5:
                results.append(text)
        for child in node.children:
            results.extend(_walk(child))
        return results

    return _walk(doctree)


def _colour_gradient(ratio: float) -> str:
    """Interpolate red (0.0) → yellow (0.5) → green (1.0)."""
    if ratio < 0.5:
        r = 255
        g = int(510 * ratio)
        b = 0
    else:
        r = int(510 * (1.0 - ratio))
        g = 255
        b = 0
    return f"#{r:02x}{g:02x}{b:02x}"


def _paragraph_diff_html(name: str, db_paras: list[str],
                         rst_paras: list[str]) -> str:
    """Build an HTML diff table comparing DB and RST paragraph lists."""

    def _short(text: str, max_len: int = 100) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len] + "…"

    lines: list[str] = []
    lines.append(f"<br><h3>Paragraph‑by‑paragraph diff for {name}</h3>")
    lines.append(
        f"<p><strong>DB:</strong> {len(db_paras)} paragraphs  "
        f"&nbsp;|&nbsp; "
        f"<strong>RST:</strong> {len(rst_paras)} paragraphs</p>"
    )

    matcher = difflib.SequenceMatcher(
        None,
        db_paras,
        rst_paras,
    )

    lines.append(
        "<table class='para-diff'>"
        "<tr><th>Change</th><th>DB Paragraph</th><th>RST Paragraph</th></tr>"
    )

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            for k in range(max(i2 - i1, j2 - j1)):
                db_text = (
                    _short(db_paras[i1 + k])
                    if i1 + k < i2 else "—"
                )
                rst_text = (
                    _short(rst_paras[j1 + k])
                    if j1 + k < j2 else "—"
                )
                lines.append(
                    "<tr>"
                    f"<td class='change-type changed'>changed</td>"
                    f"<td class='db-cell'>{_short(db_text, 200)}</td>"
                    f"<td class='rst-cell'>{_short(rst_text, 200)}</td>"
                    "</tr>"
                )
        elif tag == "delete":
            for k in range(i1, i2):
                lines.append(
                    "<tr>"
                    f"<td class='change-type removed'>removed</td>"
                    f"<td class='db-cell'>{_short(db_paras[k], 200)}</td>"
                    "<td class='rst-cell'>—</td>"
                    "</tr>"
                )
        elif tag == "insert":
            for k in range(j1, j2):
                lines.append(
                    "<tr>"
                    f"<td class='change-type added'>added</td>"
                    "<td class='db-cell'>—</td>"
                    f"<td class='rst-cell'>{_short(rst_paras[k], 200)}</td>"
                    "</tr>"
                )

    lines.append("</table>")
    return "\n".join(lines)


def _build_html(
    summary_rows: list[str],
    detail_blocks: list[str],
) -> str:
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Article Comparison Report</title>",
        "<style>",
        "  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',",
        "         Roboto, sans-serif; max-width: 1100px; margin: .5em auto;",
        "         padding: 1em; }",
        "  h1 { border-bottom: 2px solid #333; padding-bottom: .3em; }",
        "  h2 { margin-top: 1.5em; }",
        "  h3 { margin: 1em 0 .3em; }",
        "  table { border-collapse: collapse; margin: .5em 0; }",
        "  th, td { padding: .4em .8em; text-align: left; }",
        "  th { background: #eee; position: sticky; top: 0; }",
        "  .ratio { font-family: monospace; font-weight: bold; }",
        "  details { margin: .5em 0; border: 1px solid #ccc;",
        "            border-radius: 4px; overflow: hidden; }",
        "  details summary { padding: .5em .8em; cursor: pointer;",
        "                    background: #f5f5f5; }",
        "  .word-list { font-family: monospace; font-size: .85em;",
        "               max-height: 30vh; overflow: auto; padding: .5em;",
        "               background: #fafafa; border: 1px solid #eee;",
        "               word-break: break-all; }",
        "  .removed { color: #c00; }",
        "  .added   { color: #060; }",
        "  .changed { color: #c80; }",
        "  .stats td { font-family: monospace; }",
        "  .mid { background: #fea; }",
        "  .para-diff { width: 100%; }",
        "  .para-diff td { vertical-align: top;",
        "                  font-size: .85em; max-width: 40vw; }",
        "  .para-diff .change-type { width: 6em; font-weight: bold; ",
        "                          text-align: center; }",
        "  .db-cell { border-right: 2px solid #ddd; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Article Comparison Report</h1>",
        "<p>",
        "Compares the content of original web articles (syllabus sources) ",
        "against the book's RST versions using <strong>word‑set Jaccard ",
        "similarity</strong>.  This measures what fraction of all unique ",
        "words appear in <em>both</em> sources — independent of formatting, ",
        "paragraph breaks, and structural differences.",
        "</p>",
        "<p>Articles below <strong>95%</strong> also include a ",
        "<strong>paragraph‑by‑paragraph diff</strong> for deeper inspection.",
        "</p>",
        "<h2>Summary</h2>",
        "<table>",
        "<tr><th>Article</th><th>DB Words</th><th>RST Words</th>",
        "<th>Shared</th><th>Jaccard</th></tr>",
    ]
    parts.extend(summary_rows)
    parts.append("</table>")

    if detail_blocks:
        parts.append("<h2>Details — words present in only one source</h2>")
        parts.extend(detail_blocks)

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)


def main() -> None:
    if not DB_PATH.exists():
        print(
            f"{DB_PATH} not found.  Run 'make db' or "
            "'python -m intro_to_socialism.build_db' first."
        )
        return

    conn = sqlite3.connect(str(DB_PATH))
    db_articles = conn.execute(
        "SELECT name, url FROM articles ORDER BY name"
    ).fetchall()

    results: list[dict] = []

    for name, url in db_articles:
        db_text = _load_db_text(conn, name)
        rst_text = _load_rst_text(name)

        db_words = _words(db_text)
        rst_words = _words(rst_text)

        shared = db_words & rst_words
        only_db = db_words - rst_words
        only_rst = rst_words - db_words

        jac = _jaccard(db_words, rst_words)
        pct = jac * 100

        results.append({
            "name": name,
            "url": url,
            "db_words": db_words,
            "rst_words": rst_words,
            "shared": shared,
            "only_db": only_db,
            "only_rst": only_rst,
            "jac": jac,
            "pct": pct,
        })

    results.sort(key=lambda r: r["jac"])

    summary_rows: list[str] = []
    detail_blocks: list[str] = []

    for r in results:
        name = r["name"]
        db_words = r["db_words"]
        rst_words = r["rst_words"]
        shared = r["shared"]
        only_db = r["only_db"]
        only_rst = r["only_rst"]
        jac = r["jac"]
        pct = r["pct"]
        colour = _colour_gradient(jac)

        if not only_db and not only_rst:
            tag = "Identical"
        else:
            tag = f"{pct:.1f}%"

        summary_rows.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td class='stats'>{len(db_words):,}</td>"
            f"<td class='stats'>{len(rst_words):,}</td>"
            f"<td class='stats'>{len(shared):,}</td>"
            f"<td class='ratio' style='background:{colour}'>{tag}</td>"
            f"</tr>"
        )
        print(f"  {name}: {tag}  "
              f"(DB={len(db_words)} RST={len(rst_words)} "
              f"shared={len(shared)})",
              flush=True)

        detail_parts: list[str] = []
        detail_parts.append(
            f"<details><summary>{name} — "
            f"{pct:.1f}% Jaccard similarity</summary>"
        )

        if only_db or only_rst:
            detail_parts.append(
                "<table><tr><th>Only in Web Source</th>"
                "<th>Only in RST Book</th></tr><tr><td>"
            )
            if only_db:
                detail_parts.append(
                    "<div class='word-list removed'>"
                    + " ".join(sorted(only_db))
                    + "</div>"
                )
            else:
                detail_parts.append("<span class='added'>— none —</span>")
            detail_parts.append("</td><td>")
            if only_rst:
                detail_parts.append(
                    "<div class='word-list added'>"
                    + " ".join(sorted(only_rst))
                    + "</div>"
                )
            else:
                detail_parts.append("<span class='removed'>— none —</span>")
            detail_parts.append("</td></tr></table>")

        if jac < 0.95:
            db_paras = _load_db_paragraphs(conn, name)
            rst_paras = _load_rst_paragraphs(name)
            detail_parts.append(
                _paragraph_diff_html(name, db_paras, rst_paras)
            )

        detail_parts.append("</details>")
        detail_block = "".join(detail_parts)

        if only_db or only_rst or jac < 0.95:
            detail_blocks.append(detail_block)

    conn.close()

    html = _build_html(summary_rows, detail_blocks)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(
        f"\nReport written to {OUTPUT_PATH.resolve()} "
        f"({len(detail_blocks)} article(s) with differences)"
    )


if __name__ == "__main__":
    main()
