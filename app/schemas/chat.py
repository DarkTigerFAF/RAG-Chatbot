from __future__ import annotations
from pydantic import BaseModel, SecretStr
from datetime import datetime
from pydantic import ConfigDict
from typing import Any, Protocol, List

# External types used for stronger typing of the service bundle
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)


class ChatRequest(BaseModel):
    query: str


class ModelConfig(BaseModel):
    service_id: str
    chat_deployment: str


class EmbeddingConfig(BaseModel):
    embed_deployment: str


class AzureConfig(BaseModel):
    endpoint: str
    api_key: SecretStr
    api_version: str

    # Azure Cognitive Search
    search_endpoint: str
    search_key: str
    index_name: str


class RetrievedChunk(BaseModel):
    content: str


class ChatResponse(BaseModel):
    answer: str


class HistoryPair(BaseModel):
    question: str
    answer: str
    created_at: datetime


class ChatServiceCreateResponse(BaseModel):
    created: bool


class ServiceBundle(BaseModel):
    chat_service: ChatCompletionClientBase
