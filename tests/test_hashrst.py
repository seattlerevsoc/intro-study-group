import pytest

from intro_to_socialism.hashrst import content_hash, normalize


class TestNormalize:
    def test_lowercases(self):
        assert normalize("HELLO World") == "hello world"

    def test_preserves_punctuation(self):
        result = normalize("Hello, world! How are you?")
        assert "," in result
        assert "!" in result
        assert "?" in result

    def test_collapses_whitespace(self):
        result = normalize("hello   \t\n   world")
        assert result == "hello world"

    def test_strips_rst_markup(self):
        text = "**bold** and *italic* and ``code``"
        result = normalize(text)
        assert "**" not in result
        assert "bold" in result
        assert "italic" in result
        assert "code" in result

    def test_empty_string(self):
        assert normalize("") == ""


class TestContentHash:
    def test_same_input_same_hash(self):
        h1 = content_hash("Hello world")
        h2 = content_hash("Hello world")
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = content_hash("Hello world")
        h2 = content_hash("Goodbye world")
        assert h1 != h2

    def test_is_hex_string(self):
        h = content_hash("test")
        assert len(h) == 128
        assert all(c in "0123456789abcdef" for c in h)

    def test_case_insensitive_content_stability(self):
        h1 = content_hash("HELLO WORLD")
        h2 = content_hash("hello world")
        assert h1 == h2

    def test_whitespace_variants_stable(self):
        h1 = content_hash("hello  world")
        h2 = content_hash("hello world")
        assert h1 == h2

    def test_rst_markup_variants_stable(self):
        h1 = content_hash("**hello world**")
        h2 = content_hash("hello world")
        assert h1 == h2
