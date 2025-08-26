from __future__ import annotations

from typing import List
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from ...schemas.chat import AzureConfig, RetrievedChunk
from .embedding_service import AzureOpenAIEmbeddingService


class VectorSearchRetriever:
    def __init__(self, cfg: AzureConfig, embedder: AzureOpenAIEmbeddingService):
        self._embedder = embedder
        self._client = SearchClient(
            endpoint=cfg.search_endpoint,
            index_name=cfg.index_name,
            credential=AzureKeyCredential(cfg.search_key),
        )

    async def retrieve(self, question: str, *, k: int = 2) -> List[RetrievedChunk]:
        vec = await self._embedder.embed(question)
        vq = VectorizedQuery(vector=vec, k_nearest_neighbors=k, fields="content_vector")

        results = await self._client.search(
            search_text=question,
            vector_queries=[vq],
            top=k,
            select=["content"],
            query_type="semantic",
            semantic_configuration_name="semconf",
        )

        out: List[RetrievedChunk] = []
        async for r in results:
            content = (r.get("content") or "").strip()
            if content:
                out.append(RetrievedChunk(content=content))
        return out
