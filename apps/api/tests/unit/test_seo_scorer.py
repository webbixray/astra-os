import pytest

from app.application.use_cases.ai.seo_scorer import SEOScorer


@pytest.fixture
def scorer():
    return SEOScorer()


class TestSEOScorer:
    def test_empty_content_returns_zero(self, scorer):
        result = scorer.score("")
        assert result["score"] == 0
        assert result["details"]["error"] == "Empty content"

    def test_whitespace_only_returns_zero(self, scorer):
        result = scorer.score("   \n  \t  ")
        assert result["score"] == 0

    def test_short_content_scores_low(self, scorer):
        result = scorer.score("Hello world")
        assert result["score"] < 50
        assert result["details"]["word_count"] == 2

    def test_long_content_word_count(self, scorer):
        content = "This is a sentence. " * 500
        result = scorer.score(content)
        assert result["details"]["word_count"] == 2000

    def test_length_score_ranges(self, scorer):
        assert scorer._score_length(50) < 30
        assert scorer._score_length(200) > 30
        assert scorer._score_length(500) > 60
        assert scorer._score_length(1000) == 90
        assert scorer._score_length(3000) > 90

    def test_readability_empty_input(self, scorer):
        assert scorer._score_readability([], [], 0) == 0

    def test_readability_simple_words(self, scorer):
        words = ["the", "cat", "sat", "on", "the", "mat"]
        sentences = ["the cat sat on the mat"]
        score = scorer._score_readability(words, sentences, 1)
        assert 0 <= score <= 100

    def test_keyword_density_optimal(self, scorer):
        content = "python python python is python great python for python"  # 8 words, "python" ~ 6/8 = 75%
        result = scorer._score_keywords(content, ["python"], 8)
        assert result["details"]["python"]["density"] > 3
        assert result["details"]["python"]["score"] < 50

    def test_keyword_density_low(self, scorer):
        content = "python is great for programming"
        result = scorer._score_keywords(content, ["python"], 5)
        assert result["details"]["python"]["density"] == 20.0
        assert result["details"]["python"]["count"] == 1

    def test_keyword_density_under_optimal(self, scorer):
        content = "the quick brown fox jumps over the lazy dog near the river bank"
        result = scorer._score_keywords(content, ["python"], 10)
        assert result["details"]["python"]["density"] == 0
        assert result["details"]["python"]["count"] == 0

    def test_keyword_density_zero(self, scorer):
        content = "no keywords here at all"
        result = scorer._score_keywords(content, ["python"], 5)
        assert result["details"]["python"]["density"] == 0
        assert result["details"]["python"]["count"] == 0

    def test_headings_present_short_content(self, scorer):
        content = "# Heading\nSome content"
        result = scorer._score_headings(content, 50)
        assert result["has_headings"] is True
        assert result["score"] > 0

    def test_headings_no_headings_long_content(self, scorer):
        content = "no " * 1000
        result = scorer._score_headings(content, 1000)
        assert result["has_headings"] is False
        assert result["score"] < 50

    def test_headings_multiple_ideal(self, scorer):
        content = "# H1\n\n## H2\n\n### H3\n\n" + "body " * 200
        result = scorer._score_headings(content, 200)
        assert result["has_headings"] is True
        assert result["score"] > 0

    def test_syllables_counts(self, scorer):
        assert scorer._syllables("the") == 1
        assert scorer._syllables("beautiful") == 3
        assert scorer._syllables("") == 1
        assert scorer._syllables("!!!") == 1

    def test_rating_labels(self, scorer):
        assert scorer._rating(95) == "excellent"
        assert scorer._rating(80) == "good"
        assert scorer._rating(60) == "average"
        assert scorer._rating(40) == "poor"
        assert scorer._rating(10) == "bad"

    def test_keyword_scoring_with_multiple_keywords(self, scorer):
        content = "python is great and rust is fast and python is popular"
        result = scorer._score_keywords(content, ["python", "rust"], 10)
        assert "python" in result["details"]
        assert "rust" in result["details"]
        assert result["details"]["python"]["density"] > 0
        assert result["details"]["rust"]["density"] > 0
