import pytest

from intro_to_socialism import strip_rst, word_count as rst_wc
from intro_to_socialism.rst2xhtml import convert_rst_to_xhtml
from intro_to_socialism.htmlwc import word_count as html_wc
from intro_to_socialism.hashrst import content_hash as rst_hash
from intro_to_socialism.hashhtml import content_hash as html_hash


class TestSimpleConversion:
    def test_plain_paragraph(self):
        rst = "This is a simple paragraph."
        xhtml = convert_rst_to_xhtml(rst)
        assert "simple paragraph" in xhtml
        assert "<html" not in xhtml

    def test_preserves_word_count(self):
        rst = "one two three four five"
        assert rst_wc(rst) == 5
        xhtml = convert_rst_to_xhtml(rst)
        assert html_wc(xhtml) == 5

    def test_paragraph_line_breaks(self):
        rst = "First paragraph.\n\nSecond paragraph."
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)


class TestInlineMarkup:
    def test_bold(self):
        rst = "Hello **bold** world"
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_italic(self):
        rst = "Hello *italic* world"
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_literal(self):
        rst = "Hello ``code`` world"
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)


class TestStructuralElements:
    def test_title(self):
        rst = """My Title
========
Body text here."""
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_section(self):
        rst = """Section
-------
Body text."""
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_bullet_list(self):
        rst = """- item one
- item two
- item three"""
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_enumerated_list(self):
        rst = """1. first
2. second
3. third"""
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_blockquote(self):
        rst = "    This is a blockquote."
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)


class TestComplexContent:
    def test_mixed_markup(self):
        rst = """Title
=====

This paragraph has **bold** and *italic* and ``code``

- A bullet point with *emphasis*
- Another with **strong** text

A final paragraph"""
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_multiple_sections(self):
        rst = """Chapter
=======

Section One
-----------
Body of section one with **bold**

Section Two
-----------
Body of section two with *italic*"""
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)


class TestRealisticArticles:
    def test_single_sentence(self):
        rst = (
            "Revolutionary socialists believe that the working class "
            "must organize independently to overthrow capitalism"
        )
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)

    def test_citations(self):
        rst = (
            "The history of all hitherto existing society is the history "
            "of class struggles"
        )
        xhtml = convert_rst_to_xhtml(rst)
        assert rst_wc(rst) == html_wc(xhtml)
        assert rst_hash(rst) == html_hash(xhtml)
