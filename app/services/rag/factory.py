from __future__ import annotations

import os
import asyncio
import time
from typing import Tuple, Dict

from sqlalchemy.orm import Session
import semantic_kernel as sk

# from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai import FunctionChoiceBehavior

from ...schemas.chat import AzureConfig, ModelConfig, ServiceBundle, EmbeddingConfig
from .vector_retriever import VectorSearchRetriever
from .chat_history_service import ChatHistoryService
from .plugins import VectorSearchPlugin
from .service_config import load_azure_config_from_env, load_embedding_config_from_env
from .service_registry import load_model_cfg
from .chat_service import create_chat_service


_CACHED_CHAT_SERVICES: Dict[str, ServiceBundle] = {}

_CACHED_MODEL_CONFIG: Dict[str, ModelConfig] = {}
_CHAT_ANSWER_CACHE: Dict[str, tuple[float, str]] = {}
_CHAT_CACHE_TTL_SEC = 45

az_cfg = load_azure_config_from_env()
emb_cfg = load_embedding_config_from_env()

kernel = sk.Kernel()

execution_settings = AzureChatPromptExecutionSettings()
execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
execution_settings.max_tokens = 256  # cap output to reduce latency

retriever = VectorSearchRetriever(az_cfg)

# Plugins
kernel.add_plugin(plugin=VectorSearchPlugin(retriever), plugin_name="retrieval")

async def rag_chat(db: Session, user_id: int, question: str, service_id: str) -> str:
    model_cfg = _CACHED_MODEL_CONFIG.get(service_id) or load_model_cfg(db, service_id)
    if not model_cfg:
        raise ValueError(f"Chat service {service_id} not found in DB")
    _CACHED_MODEL_CONFIG[service_id] = model_cfg

    cache_key = service_id

    bundle = _CACHED_CHAT_SERVICES.get(cache_key)
    if bundle is None:
        chat_service = create_chat_service(model_cfg=model_cfg, azg_cfg=az_cfg)
        kernel.add_service(chat_service)
        bundle = ServiceBundle(chat_service=chat_service)
        _CACHED_CHAT_SERVICES[cache_key] = bundle

    history_store = ChatHistoryService()
    chat_history = await history_store.build_context(db=db, user_id=user_id, limit=8)
    chat_history.add_user_message(question)

    answer = await bundle.chat_service.get_chat_message_content(
        chat_history=chat_history,
        settings=execution_settings,
        kernel=kernel,
    )

    answer_text = answer.content or (answer.items[0].text if answer.items else "")

    asyncio.create_task(
        history_store.persist_pair(
            user_id=user_id,
            question=question,
            answer=answer_text,
        )
    )

    return answer_text
