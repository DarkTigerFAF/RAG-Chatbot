from __future__ import annotations

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)

from ...schemas.chat import AzureConfig, ModelConfig


def create_chat_service(model_cfg: ModelConfig, azg_cfg: AzureConfig) -> ChatCompletionClientBase:
    return AzureChatCompletion(
        service_id=model_cfg.service_id,
        deployment_name=model_cfg.chat_deployment,
        endpoint=azg_cfg.endpoint,
        api_key=azg_cfg.api_key.get_secret_value(),
        api_version=azg_cfg.api_version,
    )
