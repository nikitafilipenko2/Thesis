from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer


class ExtractiveSummarizer:
    def __init__(self, method='textrank'):
        self.method = method
        if method == 'textrank':
            self.summarizer = TextRankSummarizer()
        elif method == 'lsa':
            self.summarizer = LsaSummarizer()
        elif method == 'lexrank':
            self.summarizer = LexRankSummarizer()
        else:
            self.summarizer = TextRankSummarizer()

    def summarize(self, text, sentences_count=5):
        print("Method called")
        parser = PlaintextParser.from_string(text, Tokenizer("russian"))
        summary = self.summarizer(parser.document, sentences_count)
        return ' '.join([str(sentence) for sentence in summary])