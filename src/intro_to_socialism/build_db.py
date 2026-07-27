"""Fetch syllabus articles from the web and store paragraph text in SQLite."""

import json
import re
import sqlite3
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

DB_PATH = Path("articles.db")

SHORTCODE_RE = re.compile(r"\[/?et_pb[^\]]*\]")

MULTI_PAGE: dict[str, str] = {
    "27_two_souls_of_socialism": (
        "https://www.marxists.org/archive/draper/1966/twosouls/"
    ),
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

ARTICLES: dict[str, str] = {
    "1_revolutionary_socialism_an_introduction": (
        "https://medium.com/@sleigh1917/"
        "revolutionary-socialism-an-introduction-aee313a586d1"
    ),
    "2_why_the_working_class": (
        "https://socialistworker.org/2012/09/14/why-the-working-class"
    ),
    "3_where_does_profit_come_from_what_is_exploitation": (
        "https://medium.com/@sleigh1917/"
        "on-exploitation-excerpts-from-a-peoples-guide-to-capitalism-haymarket-books-149521615ea9"
    ),
    "4_socialism_needs_democracy": (
        "https://firebrand.red/2023/06/socialism-needs-democracy/"
    ),
    "5_socialists_and_the_rank_and_file_strategy": (
        "https://socialistworker.org/2018/12/13/"
        "socialists-and-the-rank-and-file-strategy"
    ),
    "6_marxism_and_oppression": (
        "https://www.marxists.org/history/etol/writers/damato/1999/xx/oppression.htm"
    ),
    "7_lessons_of_black_freedom_struggle": (
        "https://socialistworker.org/2016/02/17/"
        "lessons-for-the-new-black-freedom-struggle"
    ),
    "8_native_liberation": (
        "https://isj.org.uk/turtle-island/"
    ),
    "9_revolutionaries_and_electoral_politics": (
        "https://firebrand.red/2024/03/"
        "out-of-the-voting-booth-into-the-streets-revolutionaries-and-electoral-politics/"
    ),
    "10_why_socialists_dont_vote": (
        "https://firebrand.red/2024/08/"
        "why-socialists-dont-vote-for-our-enemies/"
    ),
    "11_chile_73": (
        "https://www.leftvoice.org/chile-73-was-victory-possible/"
    ),
    "12_what_kind_of_abolitionism": (
        "https://firebrand.red/2023/06/"
        "what-kind-of-abolitionism-can-prisons-and-police-be-abolished-under-capitalism/"
    ),
    "13_palestinian_liberation_by_any_means_necessary": (
        "https://firebrand.red/2023/10/"
        "palestinian-liberation-by-any-means-necessary/"
    ),
    "14_what_will_it_take_to_liberate_palestine": (
        "https://firebrand.red/2024/02/"
        "what-will-it-take-to-liberate-palestine/"
    ),
    "15_notes_on_marxism_and_nationalism": (
        "https://medium.com/@sleigh1917/"
        "notes-on-marxism-and-nationalism-b7849b63aa9a"
    ),
    "16_path_to_socialism_border_abolition": (
        "https://www.puntorojomag.org/2021/07/06/"
        "the-path-to-socialism-requires-border-abolition/"
    ),
    "17_lenin_bukharin_imperialism": (
        "https://isreview.org/issue/100/"
        "lenin-and-bukharin-imperialism/"
    ),
    "18_marxism_and_nationalism_part1": (
        "https://isreview.org/issues/13/"
        "marxism_nationalism_part1/"
    ),
    "19_marxism_and_nationalism_part2": (
        "https://isreview.org/issues/14/"
        "marxism_nationalism_part2/"
    ),
    "20_what_is_a_vanguard_party": (
        "https://socialistworker.org/2012/07/20/"
        "what-is-a-vanguard-party"
    ),
    "21_in_defense_of_revolutionary_organization": (
        "https://firebrand.red/2023/06/"
        "in-defense-of-revolutionary-organization/"
    ),
    "22_party_and_class": (
        "https://www.marxists.org/archive/harman/1968/xx/"
        "partyclass.htm"
    ),
    "23_points_of_unity": (
        "https://firebrand.red/points-of-unity/"
    ),
    "24_srs_and_the_left": (
        "https://sleigh1917.medium.com/"
        "firebrand-communists-and-the-revolutionary-left-3edf7f704d6d"
    ),
    "25_maoism_marxism": (
        "https://firebrand.red/2024/11/how-should-marxists-relate-to-maoism/"
    ),
    "26_ultra_leftism": (
        "https://medium.com/@sleigh1917/"
        "the-marxist-method-f43bf68ef204"
    ),
    "27_two_souls_of_socialism": (
        "https://www.marxists.org/archive/draper/1966/twosouls/"
    ),
    "28_should_socialist_groups_unite": (
        "https://sleigh1917.medium.com/"
        "should-socialist-groups-unite-0e0ca34d0c37"
    ),
    "29_disorders_of_the_left_kind": (
        "https://isreview.org/issues/37/infantile/"
    ),
    "30_marxism_oppression_identity_politics": (
        ""  # source is a local .docx file, see LOCAL_SOURCES
    ),
}

LOCAL_SOURCES: dict[str, str] = {
    "30_marxism_oppression_identity_politics": (
        "rst/articles/30_marxism_oppression_identity_politics.docx"
    ),
}


def fetch_url(url: str) -> tuple[str, bytes]:
    """Fetch a URL. Returns (content_type, body_bytes)."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        ct = resp.headers.get_content_type() or ""
    return ct, body


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1]


def _fetch_wp_api(url: str) -> str | None:
    """Fetch article content via WordPress REST API. Returns rendered HTML."""
    slug = _slug_from_url(url)
    for resource in ("posts", "pages"):
        api_url = (
            f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            f"/wp-json/wp/v2/{resource}?slug={slug}"
        )
        try:
            _, body = fetch_url(api_url)
            data = json.loads(body)
            if data:
                rendered = data[0].get("content", {}).get("rendered", "")
                if rendered:
                    return rendered
        except Exception:
            continue
    return None


def _strip_shortcodes(html_text: str) -> str:
    return SHORTCODE_RE.sub("", html_text)


def _extract_paragraphs_from_html_text(html_text: str) -> list[str]:
    """Extract paragraphs from an HTML or shortcode-rich string."""
    soup = BeautifulSoup(html_text, "html.parser")
    paragraphs: list[str] = []
    for tag in soup.find_all(
        ["p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "li", "pre"]
    ):
        text = tag.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        if text and len(text) > 10:
            paragraphs.append(text)
    return paragraphs


def extract_paragraphs_html(html_bytes: bytes) -> list[str]:
    """Extract paragraphs from raw HTML bytes."""
    soup = BeautifulSoup(html_bytes, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "iframe", "form", "figure"]):
        tag.decompose()

    content_selectors = [
        "article",
        '[role="main"]',
        "main",
        ".post-content",
        ".entry-content",
        ".article-content",
        ".content-body",
        ".entry",
        ".post",
        "#content",
        ".content",
    ]
    body = None
    for sel in content_selectors:
        body = soup.select_one(sel)
        if body:
            break
    if body is None:
        body = soup.body or soup

    return _extract_paragraphs_from_html_text(str(body))


def extract_paragraphs_pdf(pdf_bytes: bytes) -> list[str]:
    """Extract paragraphs from a PDF using pdftotext."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(pdf_bytes)
        tf.flush()
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", tf.name, "-"],
                capture_output=True,
                text=True,
            )
            text = result.stdout
        finally:
            Path(tf.name).unlink()

    blocks = re.split(r"\n\s*\n", text.strip())
    paragraphs: list[str] = []
    for block in blocks:
        cleaned = re.sub(r"\s+", " ", block).strip()
        if len(cleaned) > 10:
            paragraphs.append(cleaned)
    return paragraphs


def extract_paragraphs_docx(path: Path) -> list[str]:
    """Extract paragraphs from a .docx file."""
    from docx import Document

    doc = Document(str(path))
    paragraphs: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text and len(text) > 10:
            paragraphs.append(text)
    return paragraphs


def init_db(db_path: Path) -> sqlite3.Connection:
    """Create the database and return a connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paragraphs (
            id INTEGER PRIMARY KEY,
            article_id INTEGER NOT NULL REFERENCES articles(id),
            paragraph_num INTEGER NOT NULL,
            text TEXT NOT NULL,
            UNIQUE(article_id, paragraph_num)
        )
    """)
    return conn


def store_article(
    conn: sqlite3.Connection,
    name: str,
    url: str,
    paragraphs: list[str],
) -> int:
    """Store an article and its paragraphs. Returns article_id."""
    conn.execute("DELETE FROM paragraphs WHERE article_id IN ("
                 "SELECT id FROM articles WHERE name = ?)", (name,))
    conn.execute("DELETE FROM articles WHERE name = ?", (name,))
    cur = conn.execute(
        "INSERT INTO articles (name, url) VALUES (?, ?)",
        (name, url),
    )
    article_id = cur.lastrowid
    for i, para in enumerate(paragraphs, 1):
        conn.execute(
            "INSERT INTO paragraphs (article_id, paragraph_num, text) "
            "VALUES (?, ?, ?)",
            (article_id, i, para),
        )
    return article_id


def _fetch_marxists_multi_page(base_url: str) -> list[str]:
    """Fetch a multi-page work from marxists.org by following chapter links."""
    _, body = fetch_url(base_url)
    soup = BeautifulSoup(body, "html.parser")

    seen: set[str] = set()
    chapter_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".htm") and not href.startswith("http") and "../" not in href:
            if href not in seen:
                seen.add(href)
                chapter_urls.append(base_url + href)

    all_paragraphs: list[str] = []
    for chapter_url in chapter_urls:
        try:
            _, body_bytes = fetch_url(chapter_url)
            all_paragraphs.extend(extract_paragraphs_html(body_bytes))
        except Exception as exc:
            print(f"    WARNING: failed to fetch {chapter_url}: {exc}")

    return all_paragraphs


def main() -> None:
    conn = init_db(DB_PATH)

    for name, url in ARTICLES.items():
        print(f"Fetching: {name}")
        host = urlparse(url).netloc
        paragraphs: list[str] = []

        if name in LOCAL_SOURCES:
            docx_path = Path(LOCAL_SOURCES[name])
            print(f"  local .docx source: {docx_path}")
            paragraphs = extract_paragraphs_docx(docx_path)
            url = str(docx_path.resolve())
        elif name in MULTI_PAGE:
            base = MULTI_PAGE[name]
            print(f"  multi-page work, fetching chapters from {base}")
            paragraphs = _fetch_marxists_multi_page(base)
        elif host in {"firebrand.red"}:
            wp_html = _fetch_wp_api(url)
            if wp_html:
                clean = _strip_shortcodes(wp_html)
                paragraphs = _extract_paragraphs_from_html_text(clean)
            else:
                print(f"  WP API fallback failed")
        else:
            try:
                content_type, body_bytes = fetch_url(url)
            except Exception as exc:
                print(f"  FAILED to fetch: {exc}")
                continue

            try:
                if "pdf" in content_type or url.lower().endswith(".pdf"):
                    paragraphs = extract_paragraphs_pdf(body_bytes)
                else:
                    paragraphs = extract_paragraphs_html(body_bytes)
            except Exception as exc:
                print(f"  FAILED to extract text: {exc}")
                continue

        if not paragraphs:
            print(f"  No paragraphs extracted")
            continue

        article_id = store_article(conn, name, url, paragraphs)
        print(f"  -> article_id={article_id}, {len(paragraphs)} paragraphs")

    conn.commit()
    conn.close()

    conn2 = sqlite3.connect(str(DB_PATH))
    row_count = conn2.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
    art_count = conn2.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn2.close()
    print(f"\nDone. {art_count} articles, {row_count} paragraphs in {DB_PATH}")


if __name__ == "__main__":
    main()
