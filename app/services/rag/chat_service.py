from __future__ import annotations

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)

from ...schemas.chat import ModelConfig as ModelCfgModel


def create_chat_service(model_cfg: ModelCfgModel) -> ChatCompletionClientBase:
    return AzureChatCompletion(
        service_id=model_cfg.service_id,
        deployment_name=model_cfg.chat_deployment,
        endpoint=model_cfg.endpoint,
        api_key=model_cfg.api_key.get_secret_value(),
        api_version=model_cfg.api_version,
    )
