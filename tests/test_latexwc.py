import pytest

from intro_to_socialism.latexwc import word_count


def _make_words(n: int) -> str:
    return " ".join(f"word{i}" for i in range(n))


class TestZeroWords:
    def test_empty(self):
        assert word_count("") == 0

    def test_config_only(self):
        text = r"""\begin{document}
\textbf{}
\emph{}
\textit{}
\section*{}
\subsection*{}
\end{document}"""
        assert word_count(text) == 0


class TestOneWord:
    def test_single_word(self):
        assert word_count("hello") == 1

    def test_whitespace_padding(self):
        assert word_count("  hello  ") == 1

    def test_inline_markup(self):
        assert word_count(r"\textbf{hello}") == 1
        assert word_count(r"\emph{hello}") == 1


class TestFiveWords:
    def test_plain(self):
        assert word_count("one two three four five") == 5

    def test_with_markup(self):
        text = r"\textbf{one} \emph{two} three \textit{four} five"
        assert word_count(text) == 5

    def test_multiline(self):
        text = "alpha\nbeta\ngamma\ndelta\nepsilon"
        assert word_count(text) == 5


class Test100Words:
    def test_plain(self):
        t = _make_words(100)
        assert word_count(t) == 100

    def test_with_latex_formatting(self):
        inner = r"\textbf{" + _make_words(100) + r"}"
        assert word_count(inner) == 100

    def test_document_wrapper(self):
        inner = _make_words(100)
        t = f"""\\documentclass{{}}
\\begin{{document}}
{inner}
\\end{{document}}
"""
        assert word_count(t) == 100


class Test1000Words:
    def test_plain(self):
        t = _make_words(1000)
        assert word_count(t) == 1000

    def test_with_heavy_markup(self):
        inner = r"\textbf{" + "} \\emph{".join(_make_words(1000).split()) + "}"
        assert word_count(inner) == 1000

    def test_paragraph_environments(self):
        inner = _make_words(1000)
        text = "".join(f"\\textbf{{{w}}}\n" for w in inner.split())
        assert word_count(text) == 1000
