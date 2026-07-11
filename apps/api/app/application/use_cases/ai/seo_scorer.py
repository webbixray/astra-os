import re
from math import floor


class SEOScorer:
    def score(self, content: str, target_keywords: list[str] | None = None) -> dict:
        if not content.strip():
            return {"score": 0, "details": {"error": "Empty content"}}

        words = content.split()
        word_count = len(words)
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences) if sentences else 1

        details: dict = {}

        length_score = self._score_length(word_count)
        details["word_count"] = word_count
        details["length_score"] = length_score
        details["length_rating"] = self._rating(length_score)

        read_score = self._score_readability(words, sentences, sentence_count)
        details["avg_word_length"] = (
            round(sum(len(w) for w in words) / word_count, 1) if word_count else 0
        )
        details["avg_sentence_length"] = round(word_count / sentence_count, 1)
        details["readability_score"] = read_score
        details["readability_rating"] = self._rating(read_score)

        keyword_score = 0
        keyword_details: dict = {}
        if target_keywords:
            keyword_density = self._score_keywords(content, target_keywords, word_count)
            keyword_score = keyword_density["score"]
            keyword_details = keyword_density

        heading_score = self._score_headings(content, word_count)
        details["has_headings"] = heading_score["has_headings"]
        details["heading_score"] = heading_score["score"]
        details["heading_rating"] = self._rating(heading_score["score"])

        total = round((length_score + read_score + keyword_score + heading_score["score"]) / 4, 1)
        details["keywords"] = keyword_details

        return {
            "score": total,
            "max_score": 100,
            "rating": self._rating(total),
            "details": details,
        }

    def _score_length(self, word_count: int) -> float:
        if word_count < 100:
            return max(0, word_count / 100 * 30)
        if word_count < 300:
            return 30 + (word_count - 100) / 200 * 30
        if word_count < 800:
            return 60 + (word_count - 300) / 500 * 30
        if word_count < 2000:
            return 90
        return min(100, 90 + (word_count - 2000) / 1000 * 10)

    def _score_readability(
        self, words: list[str], sentences: list[str], sentence_count: int
    ) -> float:
        if not words or sentence_count == 0:
            return 0
        avg_syllables = sum(self._syllables(w) for w in words) / len(words)
        avg_words_per_sentence = len(words) / sentence_count

        flesch = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables
        return max(0, min(100, (flesch + 30) / 2.3))

    def _score_keywords(self, content: str, keywords: list[str], word_count: int) -> dict:
        lower = content.lower()
        results = {}
        total_score = 0
        for kw in keywords:
            count = lower.count(kw.lower())
            density = (count / max(word_count, 1)) * 100
            if 0.5 <= density <= 3:
                kw_score = 100
            elif density < 0.5:
                kw_score = density / 0.5 * 50
            else:
                kw_score = max(0, 100 - (density - 3) * 20)
            results[kw] = {
                "count": count,
                "density": round(density, 2),
                "score": round(kw_score, 1),
            }
            total_score += kw_score

        avg = total_score / max(len(keywords), 1)
        return {"score": round(avg, 1), "details": results}

    def _score_headings(self, content: str, word_count: int) -> dict:
        headings = re.findall(r"^#{1,3}\s.+", content, re.MULTILINE)
        has_headings = len(headings) > 0
        if word_count < 100 and not has_headings:
            return {"has_headings": False, "score": 80}
        ideal = max(1, floor(word_count / 200))
        score = min(100, len(headings) / ideal * 100) if has_headings else 20
        return {"has_headings": has_headings, "score": round(score, 1)}

    def _syllables(self, word: str) -> int:
        word = word.lower().strip(".,!?;:'\"()[]{}")
        if not word:
            return 1
        count = len(re.findall(r"[aeiouy]+", word))
        return max(1, count)

    def _rating(self, score: float) -> str:
        if score >= 90:
            return "excellent"
        if score >= 70:
            return "good"
        if score >= 50:
            return "average"
        if score >= 30:
            return "poor"
        return "bad"
