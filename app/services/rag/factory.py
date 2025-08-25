from __future__ import annotations

import os
from typing import Tuple, Dict

from sqlalchemy.orm import Session
import semantic_kernel as sk

# from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai import FunctionChoiceBehavior

from ...schemas.chat import (
    AzureConfig as AzureCfgModel,
    ModelConfig as ModelCfgModel,
    ServiceBundle,
)
from .embedding_service import AzureOpenAIEmbeddingService
from .vector_retriever import VectorSearchRetriever
from .chat_history_service import ChatHistoryService
from .plugins import VectorSearchPlugin
from .service_config import load_azure_config_from_env
from .service_registry import load_model_cfg
from .chat_service import create_chat_service


_BUNDLES: Dict[str, ServiceBundle] = {}


async def rag_chat(db: Session, user_id: int, question: str, service_id: str) -> str:
    model_cfg = load_model_cfg(db, service_id)
    if not model_cfg:
        raise ValueError(f"Chat service {service_id} not found in DB")

    az_cfg = load_azure_config_from_env()

    cache_key = service_id

    bundle = _BUNDLES.get(cache_key)
    if bundle is None:
        kernel = sk.Kernel()
        embedder = AzureOpenAIEmbeddingService(model_cfg, az_cfg.embed_deployment)
        retriever = VectorSearchRetriever(az_cfg, embedder)
        chat_service = create_chat_service(model_cfg=model_cfg)
        kernel.add_service(chat_service)
        kernel.add_plugin(plugin=VectorSearchPlugin(retriever), plugin_name="retrieval")
        bundle = ServiceBundle(
            kernel=kernel, chat_service=chat_service
        )
        _BUNDLES[cache_key] = bundle

    history_store = ChatHistoryService()
    chat_history = await history_store.build_context(db=db, user_id=user_id, limit=8)
    chat_history.add_user_message(question)

    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    answer = await bundle.chat_service.get_chat_message_content(
        chat_history=chat_history,
        settings=execution_settings,
        kernel=bundle.kernel,
    )

    answer_text = answer.content or (answer.items[0].text if answer.items else "")

    await history_store.persist_pair(
        db=db, user_id=user_id, question=question, answer=answer_text
    )

    return answer_text
