from __future__ import annotations

import os
from ...schemas.chat import AzureConfig as AzureCfgModel


def load_azure_config_from_env() -> AzureCfgModel:
    return AzureCfgModel(
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
        search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY", ""),
        index_name=os.getenv("AZURE_SEARCH_INDEX", ""),
        embed_deployment=os.getenv("AOAI_EMBED_MODEL", ""),
    )
