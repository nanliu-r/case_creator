from config import config


def get_embeddings():
    """Return the embedding model configured for the project.

    Supports two providers:
    - "local": HuggingFace sentence-transformers (no API key needed)
    - "openai": OpenAI-compatible API
    """
    if config.embedding_provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        kwargs = {
            "model": config.embedding_model,
            "api_key": config.openai_api_key,
        }
        if config.openai_base_url:
            kwargs["base_url"] = config.openai_base_url
        return OpenAIEmbeddings(**kwargs)
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=config.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
