import pytest

from intro_to_socialism import strip_rst, word_count as rst_wc
from intro_to_socialism.rst2latex import convert_rst_to_latex
from intro_to_socialism.latexwc import strip_latex, word_count as latex_wc
from intro_to_socialism.hashrst import content_hash as rst_hash
from intro_to_socialism.hashlatex import content_hash as latex_hash


class TestSimpleConversion:
    def test_plain_paragraph(self):
        rst = "This is a simple paragraph."
        latex = convert_rst_to_latex(rst)
        assert "simple paragraph" in latex
        assert "\\begin{document}" not in latex

    def test_preserves_word_count(self):
        rst = "one two three four five"
        assert rst_wc(rst) == 5
        latex = convert_rst_to_latex(rst)
        assert latex_wc(latex) == 5

    def test_paragraph_line_breaks(self):
        rst = "First paragraph.\n\nSecond paragraph."
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)


class TestInlineMarkup:
    def test_bold(self):
        rst = "Hello **bold** world"
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_italic(self):
        rst = "Hello *italic* world"
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_literal(self):
        rst = "Hello ``code`` world"
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)


class TestStructuralElements:
    def test_title(self):
        rst = """My Title
========
Body text here."""
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_section(self):
        rst = """Section
-------
Body text."""
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_bullet_list(self):
        rst = """- item one
- item two
- item three"""
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_enumerated_list(self):
        rst = """1. first
2. second
3. third"""
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_blockquote(self):
        rst = "    This is a blockquote."
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)


class TestComplexContent:
    def test_mixed_markup(self):
        rst = """Title
=====

This paragraph has **bold** and *italic* and ``code``

- A bullet point with *emphasis*
- Another with **strong** text

A final paragraph"""
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_multiple_sections(self):
        rst = """Chapter
=======

Section One
-----------
Body of section one with **bold**

Section Two
-----------
Body of section two with *italic*"""
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)


class TestRealisticArticles:
    def test_single_sentence(self):
        rst = (
            "Revolutionary socialists believe that the working class "
            "must organize independently to overthrow capitalism"
        )
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)

    def test_citations(self):
        rst = (
            "The history of all hitherto existing society is the history "
            "of class struggles"
        )
        latex = convert_rst_to_latex(rst)
        assert rst_wc(rst) == latex_wc(latex)
        assert rst_hash(rst) == latex_hash(latex)


class TestFragmentMode:
    def test_strips_title_block(self):
        rst = """My Article Title
================
Body text here."""
        latex = convert_rst_to_latex(rst, fragment=True)
        assert "My Article Title" not in latex
        assert "\\maketitle" not in latex

    def test_demotes_sections_to_paragraphs(self):
        rst = """Article
=======

Introductory paragraph.

Sub Heading
-----------
Body text."""
        latex = convert_rst_to_latex(rst, fragment=True)
        assert "\\paragraph{Sub Heading}" in latex
        assert "\\section{Sub Heading}" not in latex

    def test_fragment_preserves_word_count(self):
        rst = """First paragraph with **bold** text.

Sub Heading
-----------
Second paragraph with *italic* text."""
        latex = convert_rst_to_latex(rst, fragment=True)
        assert rst_wc(rst) == latex_wc(latex)

    def test_plain_paragraph_unchanged(self):
        rst = "This is a simple paragraph."
        latex = convert_rst_to_latex(rst, fragment=True)
        assert "simple paragraph" in latex
