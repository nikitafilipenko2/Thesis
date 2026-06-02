from pathlib import Path

from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer


class ExtractiveSummarizer:
    SUMMARIZER_FACTORIES = {
        "textrank": TextRankSummarizer,
        "lsa": LsaSummarizer,
        "lexrank": LexRankSummarizer,
    }

    def __init__(self, method="textrank", language="russian"):
        if method not in self.SUMMARIZER_FACTORIES:
            raise ValueError(f"Неизвестный экстрактивный метод: {method}")
        self.language = language
        self.stemmer = Stemmer(language)
        self.summarizer = self.SUMMARIZER_FACTORIES[method](self.stemmer)
        self.summarizer.stop_words = self._load_stop_words()

    @staticmethod
    def _load_stop_words():
        stopwords_path = Path(__file__).with_name("russian_stopwords.txt")
        if not stopwords_path.exists():
            return []
        with stopwords_path.open("r", encoding="utf-8") as source:
            return [line.strip() for line in source if line.strip()]

    def summarize(self, text, sentences_count=5):
        normalized_text = " ".join((text or "").split())
        if not normalized_text:
            return ""

        parser = PlaintextParser.from_string(normalized_text, Tokenizer(self.language))
        total_sentences = len(list(parser.document.sentences))
        if total_sentences == 0:
            return ""

        target_sentences = max(1, min(int(sentences_count), total_sentences))
        summary = self.summarizer(parser.document, target_sentences)
        return " ".join(str(sentence) for sentence in summary).strip()
