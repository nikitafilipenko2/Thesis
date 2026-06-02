import warnings

import torch
from transformers import pipeline


class AbstractiveSummarizerError(Exception):
    pass


class AbstractiveSummarizer:
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

    def summarize(self, text, max_length=150, min_length=50):
        normalized_text = " ".join((text or "").split())
        if not normalized_text:
            return ""

        if min_length >= max_length:
            min_length = max(20, min_length)
            max_length = max(min_length + 10, max_length)

        if len(normalized_text) > 4000:
            normalized_text = normalized_text[:4000]

        try:
            result = self.summarizer(
                normalized_text,
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
