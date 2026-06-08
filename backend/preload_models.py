import os


def preload_nltk_resources():
    import nltk

    for resource in ("stopwords", "punkt", "punkt_tab"):
        nltk.download(resource, quiet=False)


def preload_huggingface_models():
    model_list_raw = os.getenv("PRELOAD_MODEL_LIST", "").strip()
    if not model_list_raw:
        return

    from huggingface_hub import snapshot_download
    from api.services.model_service import ABSTRACTIVE_MODELS

    configured_models = {item.strip() for item in model_list_raw.split(",") if item.strip()}
    available_models = set(ABSTRACTIVE_MODELS.keys())

    for model_name in configured_models:
        if model_name not in available_models:
            raise SystemExit(f"Unsupported model in PRELOAD_MODEL_LIST: {model_name}")
        print(f"Preloading model: {model_name}")
        snapshot_download(repo_id=model_name)


def main():
    preload_nltk_resources()
    preload_huggingface_models()
    print("Model preload completed")


if __name__ == "__main__":
    main()
