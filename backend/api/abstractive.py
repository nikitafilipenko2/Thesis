import warnings

import torch
from transformers import pipeline

from api.summarization import ExtractiveSummarizer


class AbstractiveSummarizerError(Exception):
    pass


class AbstractiveSummarizer:
    MAX_INPUT_CHARS = 4000

    def __init__(self, model_name):
        self.model_name = model_name
        self.device = 0 if torch.cuda.is_available() else -1
        self.prefilter = ExtractiveSummarizer(method="textrank")
        warnings.filterwarnings("ignore", category=UserWarning)

        try:
            self.summarizer = pipeline(
                "summarization",
                model=model_name,
                device=self.device,
                model_kwargs={"torch_dtype": torch.float32},
            )
        except Exception as error:
            raise AbstractiveSummarizerError(
                f"Не удалось загрузить модель {model_name}: {error}"
            ) from error

        if hasattr(self.summarizer.model, "config"):
            self.summarizer.model.config.max_length = 1024

    @staticmethod
    def _normalize_text(text):
        return " ".join((text or "").split())

    @staticmethod
    def _count_sentences(text):
        normalized = (text or "").replace("!", ".").replace("?", ".")
        return len([sentence for sentence in normalized.split(".") if sentence.strip()])

    def _shrink_with_textrank(self, text):
        if len(text) <= self.MAX_INPUT_CHARS:
            return text

        total_sentences = self._count_sentences(text)
        if total_sentences <= 1:
            return text[: self.MAX_INPUT_CHARS]

        target_sentences = max(1, min(total_sentences, total_sentences // 2))
        reduced_text = text

        while target_sentences >= 1:
            candidate = self.prefilter.summarize(text, target_sentences).strip()
            if candidate and len(candidate) <= self.MAX_INPUT_CHARS:
                return candidate
            if candidate:
                reduced_text = candidate
            target_sentences -= 1

        if len(reduced_text) <= self.MAX_INPUT_CHARS:
            return reduced_text

        return reduced_text[: self.MAX_INPUT_CHARS]

    def summarize(self, text, max_length=150, min_length=50):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return ""

        if min_length >= max_length:
            min_length = max(20, min_length)
            max_length = max(min_length + 10, max_length)

        prepared_text = self._shrink_with_textrank(normalized_text)

        try:
            result = self.summarizer(
                prepared_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True,
            )
        except Exception as error:
            raise AbstractiveSummarizerError(
                f"Ошибка при суммаризации моделью {self.model_name}: {error}"
            ) from error

        return result[0]["summary_text"].strip()
