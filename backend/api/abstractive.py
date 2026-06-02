import re
import warnings

import torch
from transformers import pipeline


class AbstractiveSummarizerError(Exception):
    pass


class AbstractiveSummarizer:
    CHUNK_SIZE = 2200
    CHUNK_OVERLAP = 250

    def __init__(self, model_name):
        self.model_name = model_name
        self.device = 0 if torch.cuda.is_available() else -1
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
    def _split_sentences(text):
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _build_chunks(self, text):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return []
        if len(normalized_text) <= self.CHUNK_SIZE:
            return [normalized_text]

        sentences = self._split_sentences(normalized_text)
        if not sentences:
            return [normalized_text[: self.CHUNK_SIZE]]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            candidate = f"{current_chunk} {sentence}".strip()
            if len(candidate) <= self.CHUNK_SIZE:
                current_chunk = candidate
                continue

            if current_chunk:
                chunks.append(current_chunk)
                overlap = current_chunk[-self.CHUNK_OVERLAP :].strip()
                current_chunk = f"{overlap} {sentence}".strip()
                if len(current_chunk) > self.CHUNK_SIZE:
                    chunks.append(current_chunk[: self.CHUNK_SIZE].strip())
                    current_chunk = sentence[: self.CHUNK_SIZE].strip()
            else:
                chunks.append(sentence[: self.CHUNK_SIZE].strip())

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _run_single_summary(self, text, max_length, min_length):
        try:
            result = self.summarizer(
                text,
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

    def summarize(self, text, max_length=150, min_length=50):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return ""

        if min_length >= max_length:
            min_length = max(20, min_length)
            max_length = max(min_length + 10, max_length)

        chunks = self._build_chunks(normalized_text)
        if not chunks:
            return ""

        if len(chunks) == 1:
            return self._run_single_summary(chunks[0], max_length, min_length)

        chunk_summaries = [
            self._run_single_summary(chunk, max_length, min_length)
            for chunk in chunks
        ]

        merged_summary = " ".join(summary for summary in chunk_summaries if summary.strip()).strip()
        if not merged_summary:
            return ""

        if len(merged_summary) <= self.CHUNK_SIZE:
            return self._run_single_summary(merged_summary, max_length, min_length)

        reduced_chunks = self._build_chunks(merged_summary)
        reduced_summaries = [
            self._run_single_summary(chunk, max_length, min_length)
            for chunk in reduced_chunks
        ]
        final_input = " ".join(summary for summary in reduced_summaries if summary.strip()).strip()
        if not final_input:
            return ""

        return self._run_single_summary(final_input, max_length, min_length)
