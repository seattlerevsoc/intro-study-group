import pytest

from intro_to_socialism.htmlwc import word_count


def _make_words(n: int) -> str:
    return " ".join(f"word{i}" for i in range(n))


class TestZeroWords:
    def test_empty(self):
        assert word_count("") == 0

    def test_config_only(self):
        text = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"/>
    <title></title>
    <link rel="stylesheet" href="styles.css"/>
</head>
<body>
    <div class="container"></div>
    <span id="empty"></span>
    <script>/* nothing */</script>
</body>
</html>"""
        assert word_count(text) == 0


class TestOneWord:
    def test_single_word(self):
        assert word_count("hello") == 1

    def test_whitespace_padding(self):
        assert word_count("  hello  ") == 1

    def test_inline_markup(self):
        assert word_count("<em>hello</em>") == 1
        assert word_count("<strong>hello</strong>") == 1

    def test_nested_tags(self):
        assert word_count("<p><em>hello</em></p>") == 1


class TestFiveWords:
    def test_plain(self):
        assert word_count("one two three four five") == 5

    def test_with_markup(self):
        text = "<p>one</p> <em>two</em> three <strong>four</strong> five"
        assert word_count(text) == 5

    def test_multiline(self):
        text = "alpha\nbeta\ngamma\ndelta\nepsilon"
        assert word_count(text) == 5

    def test_block_elements(self):
        text = """<body>
<h1>Title</h1>
<p>first paragraph</p>
<p>second para</p>
</body>"""
        assert word_count(text) == 5


class Test100Words:
    def test_plain(self):
        t = _make_words(100)
        assert word_count(t) == 100

    def test_in_body_with_metadata(self):
        inner = _make_words(100)
        t = f"""<?xml version="1.0"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head><title></title><meta charset="utf-8"/></head>
<body>
<p>{inner}</p>
</body>
</html>"""
        assert word_count(t) == 100

    def test_fragmented_paragraphs(self):
        words = _make_words(100).split()
        t = "\n".join(f"<p>{w}</p>" for w in words)
        assert word_count(t) == 100


class Test1000Words:
    def test_plain(self):
        t = _make_words(1000)
        assert word_count(t) == 1000

    def test_with_list_structure(self):
        words = _make_words(1000).split()
        t = "<ul>\n" + "\n".join(f"<li>{w}</li>" for w in words) + "\n</ul>"
        assert word_count(t) == 1000

    def test_full_epub_document(self):
        inner = _make_words(1000)
        t = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<link rel="stylesheet" type="text/css" href="../styles.css"/>
<title>Test Article</title>
</head>
<body>
<h3>Test Article</h3>
<p><em>By Author</em></p>
<p><em>An epigraph</em></p>
<p>{inner}</p>
<blockquote>
<p>quoted text here</p>
</blockquote>
<ul>
<li><p>bullet one</p></li>
<li><p>bullet two</p></li>
</ul>
</body>
</html>"""
        words = word_count(t)
        assert words >= 1000
