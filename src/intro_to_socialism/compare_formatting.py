"""Compare RST formatting against original article HTML formatting.

Reports discrepancies in italics, bold, blockquotes, and headers.
"""

import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

RST_DIR = Path("rst/articles")

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
    "28_should_socialist_groups_unite": (
        "https://sleigh1917.medium.com/"
        "should-socialist-groups-unite-0e0ca34d0c37"
    ),
    "29_disorders_of_the_left_kind": (
        "https://isreview.org/issues/37/infantile/"
    ),
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

SHORTCODE_RE = re.compile(r"\[/?et_pb[^\]]*\]")


def fetch_url(url: str) -> tuple[str, bytes]:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        ct = resp.headers.get_content_type() or ""
    return ct, body


def extract_formatted_segments(html_bytes: bytes) -> list[dict]:
    """Extract segments with formatting info from HTML body."""
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

    segments: list[dict] = []
    content_tags = body.find_all(
        ["p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "li", "pre"]
    )

    for tag in content_tags:
        text = tag.get_text(separator=" ").strip()
        text = re.sub(r"\s+", " ", text)
        if not text or len(text) < 10:
            continue

        formatted_runs: list[dict] = []
        _extract_runs(tag, formatted_runs)

        segments.append({
            "tag": tag.name,
            "text": text,
            "runs": formatted_runs,
        })

    return segments


def _extract_runs(tag, runs: list):
    """Recursively extract formatted text runs from HTML."""
    for child in tag.children:
        if isinstance(child, str):
            text = child.strip()
            if text:
                runs.append({
                    "bold": tag.name in ("strong", "b") or (hasattr(tag, 'name') and tag.name in ("strong", "b")),
                    "italic": tag.name in ("em", "i") or (hasattr(tag, 'name') and tag.name in ("em", "i")),
                    "text": text,
                })
        else:
            # Check for <em>, <i>, <strong>, <b>
            name = getattr(child, 'name', None)
            if name in ("em", "i"):
                text = child.get_text().strip()
                if text:
                    runs.append({"bold": False, "italic": True, "text": text})
            elif name in ("strong", "b"):
                text = child.get_text().strip()
                if text:
                    runs.append({"bold": False, "italic": True, "text": text})
            else:
                _extract_runs(child, runs)


def find_italic_phrases(html_bytes: bytes) -> set[str]:
    """Find all italicized phrases in HTML."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "iframe", "form", "figure"]):
        tag.decompose()

    italic_phrases: set[str] = set()
    for tag in soup.find_all(["em", "i"]):
        text = tag.get_text().strip()
        if len(text) > 1:
            italic_phrases.add(text)
    return italic_phrases


def find_bold_phrases(html_bytes: bytes) -> set[str]:
    """Find all bold phrases in HTML."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "iframe", "form", "figure"]):
        tag.decompose()

    bold_phrases: set[str] = set()
    for tag in soup.find_all(["strong", "b"]):
        text = tag.get_text().strip()
        # Filter out uninteresting short bolds
        if len(text) > 3:
            bold_phrases.add(text)
    return bold_phrases


def find_rst_italic_markers(rst_text: str) -> set[str]:
    """Find italic-marked text in RST (single *)."""
    # Match *text* patterns that aren't **bold**
    pattern = r'(?<!\*)\*([^*\n]+?)\*(?!\*)'
    matches = re.findall(pattern, rst_text)
    return {m.strip() for m in matches if len(m.strip()) > 1}


def find_rst_bold_markers(rst_text: str) -> set[str]:
    """Find bold-marked text in RST (**)."""
    pattern = r'\*\*([^*\n]+?)\*\*'
    matches = re.findall(pattern, rst_text)
    return {m.strip() for m in matches if len(m.strip()) > 1}


def find_rst_blockquotes(rst_text: str) -> int:
    """Count blockquote-like sections (indented paragraphs)."""
    count = 0
    for line in rst_text.split("\n"):
        if line.startswith("    ") and not line.startswith("        "):
            count += 1
    return count


def compare_article(name: str, url: str) -> dict:
    """Compare formatting for one article."""
    rst_path = RST_DIR / f"{name}.rst"
    result = {
        "name": name,
        "url": url,
        "rst_found": False,
        "fetch_ok": False,
        "html_italics": 0,
        "rst_italics": 0,
        "html_bolds": 0,
        "rst_bolds": 0,
        "missing_italics": [],
        "missing_bolds": [],
    }

    if not rst_path.exists():
        return result
    result["rst_found"] = True

    rst_text = rst_path.read_text(encoding="utf-8")

    try:
        ct, body = fetch_url(url)
        result["fetch_ok"] = True
    except Exception as e:
        result["fetch_error"] = str(e)[:100]
        return result

    # For wordpress sites using shortcodes, strip them
    html_str = body.decode("utf-8", errors="replace")
    html_str = SHORTCODE_RE.sub("", html_str)
    body = html_str.encode("utf-8")

    html_italics = find_italic_phrases(body)
    rst_italics = find_rst_italic_markers(rst_text)
    html_bolds = find_bold_phrases(body)
    rst_bolds = find_rst_bold_markers(rst_text)

    result["html_italics"] = len(html_italics)
    result["rst_italics"] = len(rst_italics)
    result["html_bolds"] = len(html_bolds)
    result["rst_bolds"] = len(rst_bolds)

    # Find italic phrases in HTML that are NOT in RST
    rst_all_text = rst_text
    for phrase in sorted(html_italics):
        if phrase not in rst_all_text:  # Simple check: does plain text appear?
            result["missing_italics"].append(phrase[:80])

    for phrase in sorted(html_bolds):
        if phrase not in rst_all_text:
            result["missing_bolds"].append(phrase[:80])

    return result


def main():
    results = []
    for i, (name, url) in enumerate(ARTICLES.items(), 1):
        print(f"[{i}/{len(ARTICLES)}] {name}...", flush=True)
        result = compare_article(name, url)
        results.append(result)

    print("\n" + "=" * 80)
    print("FORMATTING COMPARISON REPORT")
    print("=" * 80)

    issues_found = 0
    for r in results:
        if not r["rst_found"]:
            print(f"\n{r['name']}: RST FILE NOT FOUND")
            continue
        if not r["fetch_ok"]:
            print(f"\n{r['name']}: FETCH FAILED: {r.get('fetch_error', 'unknown')}")
            continue

        print(f"\n--- {r['name']} ---")
        print(f"  URL: {r['url']}")
        print(f"  HTML italics: {r['html_italics']}, RST italics: {r['rst_italics']}")
        print(f"  HTML bolds: {r['html_bolds']}, RST bolds: {r['rst_bolds']}")

        if r["missing_italics"]:
            issues_found += 1
            print(f"  MISSING ITALICS ({len(r['missing_italics'])}):")
            for phrase in r["missing_italics"][:10]:
                print(f"    - {phrase}")

        if r["missing_bolds"]:
            issues_found += 1
            print(f"  MISSING BOLDS ({len(r['missing_bolds'])}):")
            for phrase in r["missing_bolds"][:5]:
                print(f"    - {phrase}")

    print(f"\n{'=' * 80}")
    print(f"Articles with formatting issues: {issues_found} / {len(results)}")


if __name__ == "__main__":
    main()
