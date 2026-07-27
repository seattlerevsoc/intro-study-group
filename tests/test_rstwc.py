import pytest

from intro_to_socialism import word_count


def _make_words(n: int) -> str:
    return " ".join(f"word{i}" for i in range(n))


class TestZeroWords:
    def test_empty(self):
        assert word_count("") == 0

    def test_config_only(self):
        text = """.. include:: foo.rst
.. include:: bar.rst
.. _some-label:
.. _another:
:Author: Someone
:Date: 2024
"""
        assert word_count(text) == 0


class TestOneWord:
    def test_single_word(self):
        assert word_count("hello") == 1

    def test_whitespace_padding(self):
        assert word_count("  hello  ") == 1

    def test_inline_markup(self):
        assert word_count("**hello**") == 1
        assert word_count("*hello*") == 1


class TestFiveWords:
    def test_plain(self):
        assert word_count("one two three four five") == 5

    def test_with_markup(self):
        text = "**one** *two* ``three`` `four` five"
        assert word_count(text) == 5

    def test_multiline(self):
        text = "alpha\nbeta\ngamma\ndelta\nepsilon"
        assert word_count(text) == 5


class Test100Words:
    def test_plain(self):
        t = _make_words(100)
        assert word_count(t) == 100

    def test_with_rst_directives(self):
        inner = _make_words(100)
        t = f""".. include:: external.rst
.. _target:
:Author: Tester

{inner}

.. _end-label:
"""
        assert word_count(t) == 100


class Test1000Words:
    def test_plain(self):
        t = _make_words(1000)
        assert word_count(t) == 1000

    def test_with_heavy_markup(self):
        inner = "**" + "** **".join(_make_words(1000).split()) + "**"
        assert word_count(inner) == 1000

    def test_interleaved_directives(self):
        parts = []
        for i in range(1000):
            parts.append(f".. _label{i}:")
            parts.append(f":field{i}: value")
            parts.append(f"word{i}")
        text = "\n".join(parts)
        assert word_count(text) == 1000
