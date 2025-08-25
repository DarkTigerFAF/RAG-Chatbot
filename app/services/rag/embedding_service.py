from __future__ import annotations

from typing import List
from openai import AsyncAzureOpenAI

from ...schemas.chat import ModelConfig


class AzureOpenAIEmbeddingService:
    def __init__(self, cfg: ModelConfig, embed_model: str):
        self.client = AsyncAzureOpenAI(
            api_key=cfg.api_key.get_secret_value(),
            api_version=cfg.api_version,
            azure_endpoint=cfg.endpoint,
        )
        self.embed_deployment = embed_model

    async def embed(self, text: str) -> List[float]:
        resp = await self.client.embeddings.create(
            model=self.embed_deployment,
            input=[text],
        )
        return resp.data[0].embedding
