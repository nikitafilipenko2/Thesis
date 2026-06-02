import time
from dataclasses import dataclass

from api.services.model_service import (
    get_default_abstractive_model_name,
    get_model,
    is_extractive_model,
)


class SummarizationServiceError(Exception):
    pass


@dataclass
class SummaryPayload:
    input_text: str
    output_text: str
    summary_type: str
    model_name: str
    length_param: int
    processing_time: float


def _parse_extractive_length(length_param):
    if isinstance(length_param, dict):
        return 5
    return max(1, int(length_param))


def _parse_abstractive_lengths(length_param):
    if isinstance(length_param, dict):
        min_words = int(length_param.get("min", 50))
        max_words = int(length_param.get("max", 150))
    else:
        max_words = max(30, int(length_param) * 20)
        min_words = max(20, max_words // 2)

    if min_words >= max_words:
        min_words = max(20, min_words)
        max_words = max(min_words + 10, max_words)

    return min_words, max_words


def summarize_text(input_text, model_name, length_param):
    normalized_text = (input_text or "").strip()
    if not normalized_text:
        raise SummarizationServiceError("Текст не может быть пустым")

    started_at = time.time()
    summarizer = get_model(model_name)
    if summarizer is None:
        raise SummarizationServiceError(f"Модель {model_name} недоступна")

    if is_extractive_model(model_name):
        length_value = _parse_extractive_length(length_param)
        output_text = summarizer.summarize(normalized_text, length_value)
        summary_type = "extractive"
    else:
        min_words, max_words = _parse_abstractive_lengths(length_param)
        output_text = summarizer.summarize(
            normalized_text,
            max_length=max_words,
            min_length=min_words,
        )
        length_value = max_words
        summary_type = "abstractive"

    if not output_text.strip():
        raise SummarizationServiceError("Модель вернула пустой результат")

    return SummaryPayload(
        input_text=normalized_text,
        output_text=output_text,
        summary_type=summary_type,
        model_name=model_name,
        length_param=length_value,
        processing_time=time.time() - started_at,
    )


def summarize_file_text(input_text, summary_type, length_param, model_name=None):
    normalized_type = (summary_type or "").strip()
    if normalized_type == "extractive":
        selected_model = "extractive_textrank"
    elif normalized_type == "abstractive":
        selected_model = model_name or get_default_abstractive_model_name()
    else:
        raise SummarizationServiceError("Неизвестный тип суммаризации")

    return summarize_text(input_text, selected_model, length_param)
