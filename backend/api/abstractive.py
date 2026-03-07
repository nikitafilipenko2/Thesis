from transformers import pipeline
import torch


class AbstractiveSummarizer:
    def __init__(self, model_name="cointegrated/rut5-base-absum"):
        print(f"Загрузка модели {model_name}...")
        try:
            self.device = 0 if torch.cuda.is_available() else -1
            self.summarizer = pipeline(
                "summarization",
                model=model_name,
                device=self.device
            )
            print("Модель загружена!")
        except Exception as e:
            print(f"Ошибка при загрузке модели: {e}")
            self.summarizer = None

    def summarize(self, text, max_length=100, min_length=30):
        if self.summarizer is None:
            return "Модель не загружена. Проверьте ошибки выше."

        try:
            if len(text) > 2000:
                text = text[:2000]

            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            return result[0]['summary_text']
        except Exception as e:
            return f"Ошибка при суммаризации: {str(e)}"