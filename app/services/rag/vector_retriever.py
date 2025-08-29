from __future__ import annotations

from typing import List
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from ...schemas.chat import AzureConfig, RetrievedChunk


class VectorSearchRetriever:
    def __init__(self, cfg: AzureConfig):
        self._client = SearchClient(
            endpoint=cfg.search_endpoint,
            index_name=cfg.index_name,
            credential=AzureKeyCredential(cfg.search_key),
        )

    async def retrieve(self, question: str, *, k: int) -> List[RetrievedChunk]:
        result = await self._client.search(
            search_text=question,
            top=k,
            select="content",
            query_type="semantic",
            semantic_configuration_name="semconf",
        )
        return '\n'.join([doc["content"] async for doc in result])
