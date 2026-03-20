"""Azure identity helpers for the Azure-backed runtime mode."""

from __future__ import annotations

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from src.config import settings


def get_azure_credential() -> DefaultAzureCredential:
    kwargs = {
        "exclude_interactive_browser_credential": settings.identity.exclude_interactive_browser_credential,
    }
    if settings.identity.client_id:
        kwargs["managed_identity_client_id"] = settings.identity.client_id
    if settings.identity.tenant_id:
        kwargs["tenant_id"] = settings.identity.tenant_id
    return DefaultAzureCredential(**kwargs)


def build_azure_openai_client() -> AzureOpenAI:
    token_provider = get_bearer_token_provider(
        get_azure_credential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        azure_endpoint=settings.openai.endpoint,
        api_version=settings.openai.api_version,
        azure_ad_token_provider=token_provider,
    )