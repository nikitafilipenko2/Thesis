from api.abstractive import AbstractiveSummarizer, AbstractiveSummarizerError
from api.summarization import ExtractiveSummarizer


EXTRACTIVE_MODELS = {
    "extractive_textrank": {"label": "TextRank", "type": "extractive", "method": "textrank"},
    "extractive_lsa": {"label": "LSA", "type": "extractive", "method": "lsa"},
    "extractive_lexrank": {"label": "LexRank", "type": "extractive", "method": "lexrank"},
}

ABSTRACTIVE_MODELS = {
    "cointegrated/rut5-base-absum": {
        "label": "cointegrated/rut5-base-absum",
        "type": "abstractive",
    },
    "IlyaGusev/rut5_base_sum_gazeta": {
        "label": "IlyaGusev/rut5_base_sum_gazeta",
        "type": "abstractive",
    },
    "Azerotorez/Scientific_paper_rusumm": {
        "label": "Azerotorez/Scientific_paper_rusumm",
        "type": "abstractive",
    },
    "IlyaGusev/mbart_ru_sum_gazeta": {
        "label": "IlyaGusev/mbart_ru_sum_gazeta",
        "type": "abstractive",
    },
}

MODEL_REGISTRY = {**EXTRACTIVE_MODELS, **ABSTRACTIVE_MODELS}
_model_cache = {}


def get_model(model_name):
    if model_name not in MODEL_REGISTRY:
        return None
    if model_name in _model_cache:
        return _model_cache[model_name]

    model_config = MODEL_REGISTRY[model_name]
    if model_config["type"] == "extractive":
        model_instance = ExtractiveSummarizer(method=model_config["method"])
    else:
        try:
            model_instance = AbstractiveSummarizer(model_name=model_name)
        except AbstractiveSummarizerError:
            return None

    _model_cache[model_name] = model_instance
    return model_instance


def is_extractive_model(model_name):
    return model_name in EXTRACTIVE_MODELS


def get_default_abstractive_model_name():
    return next(iter(ABSTRACTIVE_MODELS))


def get_abstractive_model_choices():
    return list(ABSTRACTIVE_MODELS.items())
