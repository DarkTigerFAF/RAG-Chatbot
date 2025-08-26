from __future__ import annotations

import os
from ...schemas.chat import AzureConfig, EmbeddingConfig


def load_azure_config_from_env() -> AzureConfig:
    return AzureConfig(
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
        search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY", ""),
        index_name=os.getenv("AZURE_SEARCH_INDEX", ""),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", ""),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "")
    )
    
def load_embedding_config_from_env() -> EmbeddingConfig:
    return EmbeddingConfig(
        embed_deployment=os.getenv("AOAI_EMBED_MODEL", "")
    )

