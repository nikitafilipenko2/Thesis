from api.abstractive import AbstractiveSummarizer
from api.summarization import ExtractiveSummarizer


_models = {}


def _load_extractive_models():
    if "extractive_textrank" not in _models:
        _models["extractive_textrank"] = ExtractiveSummarizer(method="textrank")
    if "extractive_lsa" not in _models:
        _models["extractive_lsa"] = ExtractiveSummarizer(method="lsa")
    if "extractive_lexrank" not in _models:
        _models["extractive_lexrank"] = ExtractiveSummarizer(method="lexrank")


def _load_abstractive_model():
    if "abstractive_cointegrated" not in _models:
        _models["abstractive_cointegrated"] = AbstractiveSummarizer(
            model_name="cointegrated/rut5-base-absum"
        )


def get_model(model_name):
    if model_name.startswith("extractive_"):
        _load_extractive_models()
    elif model_name == "abstractive_cointegrated":
        _load_abstractive_model()
    return _models.get(model_name)
