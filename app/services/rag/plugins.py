from semantic_kernel.functions import kernel_function

from .vector_retriever import VectorSearchRetriever
from typing import Annotated


class VectorSearchPlugin:
    def __init__(self, retriever: VectorSearchRetriever):
        self._retriever = retriever

    @kernel_function(
        name="retrieve",
        description="Retrieve relevant top-k chunks for a query",
    )
    async def retrieve(
        self,
        question: Annotated[str, "The question to retrieve chunks for"],
        k: Annotated[int, "The number of chunks to retrieve"] = 2,
    ) -> str:
        chunks = await self._retriever.retrieve(question, k=k)
        text = "\n\n".join(f"[#{i+1}]\n{c.content}" for i, c in enumerate(chunks))
        # Trim to keep prompt small (approx token-aware but simple char cap)
        MAX_CHARS = 2000
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n\n..."
        return text
