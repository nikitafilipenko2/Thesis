from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.nlp.stemmers import Stemmer
import os


class ExtractiveSummarizer:
    def __init__(self, method='textrank', language='russian'):
        self.language = language
        self.stemmer = Stemmer(language)

        if method == 'textrank':
            self.summarizer = TextRankSummarizer(self.stemmer)
        elif method == 'lsa':
            self.summarizer = LsaSummarizer(self.stemmer)
        elif method == 'lexrank':
            self.summarizer = LexRankSummarizer(self.stemmer)
        else:
            self.summarizer = TextRankSummarizer(self.stemmer)

        stopwords_path = os.path.join(os.path.dirname(__file__), 'russian_stopwords.txt')
        if os.path.exists(stopwords_path):
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                stop_words = [line.strip() for line in f if line.strip()]
            self.summarizer.stop_words = stop_words

    def summarize(self, text, sentences_count=5):
        parser = PlaintextParser.from_string(text, Tokenizer(self.language))

        sentences = list(parser.document.sentences)
        print(f"Всего предложений в тексте: {len(sentences)}")

        if sentences_count > len(sentences):
            sentences_count = len(sentences)

        if sentences_count == 0:
            return ""

        summary = self.summarizer(parser.document, sentences_count)
        result = ' '.join([str(sentence) for sentence in summary])
        print(f"Выбрано предложений: {len(summary)}")
        return result