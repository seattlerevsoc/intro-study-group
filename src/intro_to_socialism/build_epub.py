#!/usr/bin/env python3
"""Convert RST syllabus to EPUB using rst2xhtml."""

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RST_DIR = Path("rst")
EPUB_DIR = Path("epub")
OEBPS_DIR = EPUB_DIR / "OEBPS"
METAINF_DIR = EPUB_DIR / "META-INF"
ARTICLES_DIR = "articles"
MAIN = "introduction_to_socialism"

DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'

PREAMBLE = f"""<?xml version="1.0" encoding="UTF-8"?>
{DOCTYPE}
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>"""

PREAMBLE_ARTICLE = f"""<?xml version="1.0" encoding="UTF-8"?>
{DOCTYPE}
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<link rel="stylesheet" type="text/css" href="../styles.css"/>
</head>
<body>"""

POSTAMBLE = "\n</body>\n</html>"

TITLE = "Introduction to Revolutionary Socialism, A Syllabus"
AUTHOR = "Seattle Revolutionary Socialists"

CSS = (
    "body { font-family: Georgia, serif; line-height: 1.6; margin: 2em; }\n"
    ".title { font-size: 2em; }\n"
    "h1 { font-size: 1.6em; margin-top: 1.5em; }\n"
    "h2 { font-size: 1.3em; margin-top: 1.2em; }\n"
    "h3 { font-size: 1.1em; margin-top: 1em; }\n"
    "h4 { font-size: 1em; font-weight: bold; margin-top: 1em; }\n"
    "p { margin: 0.5em 0; text-indent: 0; }\n"
    "blockquote { margin: 0.8em 2em; font-style: italic; }\n"
    "ul, ol { margin: 0.5em 0 0.5em 2em; }\n"
    "li { margin: 0.3em 0; }\n"
    "hr.section-divider { border: none; text-align: center; margin: 1.5em 0; }\n"
    "hr.section-divider::after { content: '* * *'; }\n"
    ".title-page { text-align: center; padding-top: 20%; }\n"
    ".title-page .author { font-size: 1.2em; color: #555; }\n"
    ".toc h1 { font-size: 1.6em; }\n"
    ".toc a { text-decoration: none; color: #036; }\n"
    ".chapter { margin-top: 2em; }\n"
    ".docutils.footnote, .footnote-reference { font-size: 0.85em; }\n"
    ".docutils.footnote td.label { vertical-align: top; }\n"
    "a.footnote-reference { vertical-align: super; font-size: 0.75em; }\n"
)


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def parse_chapter_rst(path: Path):
    """Parse a chapter .rst file for structure."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    chapter_title = None
    sections = []       # {"title": str, "articles": [str]}
    study_questions = []  # str

    current_section = None
    in_study_qs = False
    i = 0

    def finalize_section():
        nonlocal current_section
        if current_section and current_section["articles"]:
            sections.append(current_section)
        current_section = None
    """Parse a chapter .rst file for structure."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    chapter_title = None
    sections = []       # {"title": str, "articles": [str]}
    study_questions = []  # str

    current_section = None
    in_study_qs = False
    i = 0

    def finalize_section():
        nonlocal current_section
        if current_section and current_section["articles"]:
            sections.append(current_section)
        current_section = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1

        if not stripped or stripped.startswith(".. _"):  # link target
            continue

        is_heading_sep = len(stripped) >= 3 and all(c in ("=", "-") for c in stripped) and len(set(stripped)) == 1
        if is_heading_sep:
            continue

        if chapter_title is None:
            chapter_title = stripped
            continue

        if stripped.startswith(".. include::"):
            inc = stripped[len(".. include:: "):].strip()
            if current_section is not None:
                current_section["articles"].append(inc)
            continue

        if stripped == "Study Questions":
            finalize_section()
            in_study_qs = True
            current_section = None
            continue

        if in_study_qs and re.match(r"^\d+\.\s", stripped):
            study_questions.append(stripped)
            continue

        # New section header
        finalize_section()
        current_section = {"title": stripped, "articles": []}

        # Skip underline separator on next line
        if i < len(lines) and lines[i].strip() and all(c == "-" for c in lines[i].strip()):
            i += 1

    finalize_section()
    return chapter_title, sections, study_questions


def parse_all_chapters():
    """Parse all chapter files for structure from RST."""
    chapters = []
    chapter_files = sorted(RST_DIR.glob("chapter_*.rst"))
    for cf in chapter_files:
        title, sections, sqs = parse_chapter_rst(cf)
        if title and sections:
            article_groups = []
            for sec in sections:
                article_groups.append({
                    "title": sec["title"],
                    "articles": [Path(a).stem for a in sec["articles"]],
                })
            chapters.append({
                "title": title,
                "groups": article_groups,
                "study_questions": sqs,
            })
    return chapters


def extract_xhtml_body(xhtml_path):
    """Extract the body content (inside <main>) from an rst2xhtml output."""
    text = xhtml_path.read_text(encoding="utf-8")
    match = re.search(r"<main[^>]*>(.*?)</main>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"<body>(.*?)</body>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def parse_latex_titles():
    """Extract article title mapping from the LaTeX main template."""
    tex_path = Path("latex") / f"{MAIN}.tex"
    if not tex_path.exists():
        return {}
    text = tex_path.read_text(encoding="utf-8")
    titles = {}
    prev_sub = None
    for line in text.split("\n"):
        m = re.match(r"\\subsection\{(.+)\}", line.strip())
        if m:
            prev_sub = m.group(1)
        m = re.match(r"\\input\{\./articles/(.+)\}", line.strip())
        if m and prev_sub:
            key = m.group(1).replace(".tex", "")
            titles[key] = prev_sub.replace("\\&", "&").replace("\\%", "%").replace("\\$", "$")
            prev_sub = None
    return titles


def build_epub():
    EPUB_DIR.mkdir(parents=True, exist_ok=True)
    OEBPS_DIR.mkdir(parents=True, exist_ok=True)
    (OEBPS_DIR / ARTICLES_DIR).mkdir(parents=True, exist_ok=True)
    METAINF_DIR.mkdir(parents=True, exist_ok=True)

    chapters = parse_all_chapters()
    article_titles = parse_latex_titles()

    def article_label(name):
        """Get the proper display title for an article, falling back to generated."""
        if name in article_titles:
            return article_titles[name]
        label = name.replace("_", " ").title()
        return re.sub(r"^\d+\s+", "", label)

    # Collect all article RST paths
    article_paths = []
    for ch in chapters:
        for group in ch["groups"]:
            for name in group["articles"]:
                rst_path = RST_DIR / ARTICLES_DIR / f"{name}.rst"
                if rst_path.exists():
                    article_paths.append(rst_path)
                else:
                    print(f"  WARNING: {rst_path} not found")

    # Run rst2xhtml on all articles
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        print(f"Converting {len(article_paths)} articles to XHTML...")
        cmd = ["uv", "run", "rst2xhtml", "-o", str(out)] + [str(p) for p in article_paths]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"rst2xhtml stderr:\n{result.stderr}")
            result.check_returncode()

        xhtml_files = {}
        for xf in out.rglob("*.xhtml"):
            xhtml_files[xf.stem] = xf

        print(f"Found {len(xhtml_files)} XHTML files")

        for ch in chapters:
            for group in ch["groups"]:
                for name in group["articles"]:
                    if name not in xhtml_files:
                        print(f"  WARNING: no XHTML for {name}")
                        continue
                    body = extract_xhtml_body(xhtml_files[name])
                    full_html = PREAMBLE_ARTICLE + "\n" + body + "\n" + POSTAMBLE
                    out_path = OEBPS_DIR / ARTICLES_DIR / f"{name}.xhtml"
                    out_path.write_text(full_html, encoding="utf-8")

    # --- EPUB assembly ---
    manifest_items = []
    spine_items = []
    item_id_counter = [0]

    def add_item(path: Path, media_type: str, id_: str = None) -> str:
        rel = str(path.relative_to(OEBPS_DIR))
        if id_ is None:
            item_id_counter[0] += 1
            id_ = f"item{item_id_counter[0]}"
        manifest_items.append((id_, rel, media_type))
        return id_

    # --- title page ---
    title_body = '<div class="title-page">\n'
    title_body += f'<h1 class="title">{_escape(TITLE)}</h1>\n'
    title_body += f'<p class="author">{_escape(AUTHOR)}</p>\n'
    title_body += "</div>\n"
    title_fname = "title.xhtml"
    (OEBPS_DIR / title_fname).write_text(
        PREAMBLE.replace("</head>", f"<title>{_escape(TITLE)}</title>\n</head>")
        + "\n" + title_body + "\n" + POSTAMBLE,
        encoding="utf-8",
    )
    add_item(OEBPS_DIR / title_fname, "application/xhtml+xml", "title")
    spine_items.append("title")

    # --- TOC page ---
    toc_html_parts = ['<div class="toc">\n<h1>Contents</h1>\n']
    for ch in chapters:
        ch_html = f'<div class="chapter">\n<h1>{_escape(ch["title"])}</h1>\n'
        for group in ch["groups"]:
            if not group["articles"]:
                continue
            ch_html += f'<h2>{_escape(group["title"])}</h2>\n'
            for name in group["articles"]:
                art_file = f"{name}.xhtml"
                ch_html += f'<h3><a href="{ARTICLES_DIR}/{art_file}">{_escape(article_label(name))}</a></h3>\n'
        sq = ch.get("study_questions", [])
        if sq:
            ch_html += "<h2>Study Questions</h2>\n<ol>\n"
            for q in sq:
                q_text = re.sub(r"^\d+\.\s*", "", q)
                ch_html += f"<li>{_escape(q_text)}</li>\n"
            ch_html += "</ol>\n"
        ch_html += "</div>\n"
        toc_html_parts.append(ch_html)
    toc_html_parts.append("</div>")
    full_toc_body = "\n".join(toc_html_parts)
    toc_fname = "toc.xhtml"
    (OEBPS_DIR / toc_fname).write_text(
        PREAMBLE.replace("</head>", "<title>Contents</title>\n</head>")
        + "\n" + full_toc_body + "\n" + POSTAMBLE,
        encoding="utf-8",
    )
    add_item(OEBPS_DIR / toc_fname, "application/xhtml+xml", "toc")
    spine_items.append("toc")

    # --- toc tree for NCX ---
    class TocNode:
        __slots__ = ("label", "href", "children")
        def __init__(self, label, href=None):
            self.label = label
            self.href = href
            self.children = []

    toc_root = TocNode("root")
    toc_root.children.append(TocNode("Title", title_fname))
    toc_root.children.append(TocNode("Contents", toc_fname))

    for ch in chapters:
        ch_node = TocNode(ch["title"])
        for group in ch["groups"]:
            grp_node = TocNode(group["title"])
            for name in group["articles"]:
                art_xhtml = f"{name}.xhtml"
                art_path = OEBPS_DIR / ARTICLES_DIR / art_xhtml
                if art_path.exists():
                    art_id = add_item(art_path, "application/xhtml+xml")
                    spine_items.append(art_id)
                    grp_node.children.append(TocNode(article_label(name), f"{ARTICLES_DIR}/{art_xhtml}"))
            ch_node.children.append(grp_node)
        toc_root.children.append(ch_node)

    # --- CSS ---
    css_path = OEBPS_DIR / "styles.css"
    css_path.write_text(CSS, encoding="utf-8")
    add_item(css_path, "text/css", "css")

    # --- toc.ncx ---
    play_order = [0]

    def render_ncx_level(nodes, indent_depth, xml_parts):
        for node in nodes:
            play_order[0] += 1
            po = play_order[0]
            indent = "    " + "  " * indent_depth
            xml_parts.append(f'{indent}<navPoint id="navpoint-{po}" playOrder="{po}">\n')
            xml_parts.append(f'{indent}  <navLabel><text>{_escape(node.label)}</text></navLabel>\n')
            if node.href:
                xml_parts.append(f'{indent}  <content src="{_escape(node.href)}"/>\n')
            if node.children:
                render_ncx_level(node.children, indent_depth + 1, xml_parts)
            xml_parts.append(f"{indent}</navPoint>\n")

    ncx_parts = []
    render_ncx_level(toc_root.children, 0, ncx_parts)

    ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:00000000-0000-0000-0000-000000000001"/>
    <meta name="dtb:depth" content="3"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{_escape(TITLE)}</text></docTitle>
  <docAuthor><text>{_escape(AUTHOR)}</text></docAuthor>
  <navMap>
"""
    ncx += "".join(ncx_parts)
    ncx += "  </navMap>\n</ncx>\n"
    (OEBPS_DIR / "toc.ncx").write_text(ncx, encoding="utf-8")
    add_item(OEBPS_DIR / "toc.ncx", "application/x-dtbncx+xml", "ncx")

    # --- content.opf ---
    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
  <metadata>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">{_escape(TITLE)}</dc:title>
    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">{_escape(AUTHOR)}</dc:creator>
    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">en</dc:language>
    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="bookid">urn:uuid:00000000-0000-0000-0000-000000000001</dc:identifier>
  </metadata>
  <manifest>
"""
    for id_, href, media in manifest_items:
        opf += f'    <item id="{id_}" href="{href}" media-type="{media}"/>\n'
    opf += '  </manifest>\n  <spine toc="ncx">\n'
    for sid in spine_items:
        opf += f'    <itemref idref="{sid}"/>\n'
    opf += "  </spine>\n</package>\n"
    (OEBPS_DIR / "content.opf").write_text(opf, encoding="utf-8")

    # --- container.xml ---
    container = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
    (METAINF_DIR / "container.xml").write_text(container, encoding="utf-8")

    # --- mimetype ---
    (EPUB_DIR / "mimetype").write_text("application/epub+zip", encoding="utf-8")

    print(f"\nEPUB prepared at {EPUB_DIR}")
    print(f"  {len(manifest_items)} manifest items")
    print(f"  {len(spine_items)} spine items")
    print(f"  {play_order[0]} TOC entries")


def zip_epub():
    epub_path = Path(f"{MAIN}.epub")
    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zf:
        mimetype_path = EPUB_DIR / "mimetype"
        zf.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(EPUB_DIR):
            for fname in sorted(files):
                fpath = Path(root) / fname
                if fpath == mimetype_path:
                    continue
                arcname = str(fpath.relative_to(EPUB_DIR))
                zf.write(fpath, arcname)
    print(f"EPUB created: {epub_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "zip":
        zip_epub()
    else:
        build_epub()
