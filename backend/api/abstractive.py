from transformers import pipeline
import torch


class AbstractiveSummarizer:
    def __init__(self, model_name="cointegrated/rut5-base-absum"):
        print(f"Загрузка модели {model_name}...")
        try:
            self.device = -1
            self.model_name = model_name

            # Подавляем предупреждения
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning)

            self.summarizer = pipeline(
                "summarization",
                model=model_name,
                device=self.device,
                model_kwargs={"torch_dtype": torch.float32},  # для CPU
            )

            # Настраиваем генерацию, чтобы убрать ворнинг
            if hasattr(self.summarizer.model, 'config'):
                self.summarizer.model.config.max_length = 512

            print("Модель загружена!")
        except Exception as e:
            print(f"Ошибка при загрузке модели: {e}")
            self.summarizer = None

    def summarize(self, text, max_length=150, min_length=50):
        if self.summarizer is None:
            return f"Модель {self.model_name} не загрузилась"

        try:
            if len(text) > 2000:
                text = text[:2000]

            # Используем только max_length, чтобы избежать ворнинга
            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            return result[0]['summary_text']
        except Exception as e:
            return f"Ошибка при суммаризации: {str(e)}"