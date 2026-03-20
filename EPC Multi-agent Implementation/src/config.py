"""Application configuration for mock and Azure-backed runtime modes."""

from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class AzureIdentitySettings(BaseSettings):
    tenant_id: str = Field("", alias="AZURE_TENANT_ID")
    client_id: str = Field("", alias="AZURE_CLIENT_ID")
    exclude_interactive_browser_credential: bool = Field(
        False,
        alias="AZURE_EXCLUDE_INTERACTIVE_BROWSER_CREDENTIAL",
    )

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


class AzureOpenAISettings(BaseSettings):
    endpoint: str = Field("https://demo.openai.azure.com/", alias="AZURE_OPENAI_ENDPOINT")
    deployment: str = Field("gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT")
    api_version: str = Field("2024-12-01-preview", alias="AZURE_OPENAI_API_VERSION")

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


class AzurePostgreSQLSettings(BaseSettings):
    host: str = Field("localhost", alias="AZURE_POSTGRES_HOST")
    port: int = Field(5432, alias="AZURE_POSTGRES_PORT")
    database: str = Field("epckg", alias="AZURE_POSTGRES_DATABASE")
    ssl_mode: str = Field("require", alias="AZURE_POSTGRES_SSL_MODE")
    graph_name: str = Field("epc_graph", alias="AZURE_POSTGRES_GRAPH_NAME")

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}

    @property
    def server_name(self) -> str:
        return self.host.split(".")[0]


class AzureSearchSettings(BaseSettings):
    endpoint: str = Field("https://demo.search.windows.net", alias="AZURE_SEARCH_ENDPOINT")
    index: str = Field("epc-documents", alias="AZURE_SEARCH_INDEX")

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


class AzureAIServicesSettings(BaseSettings):
    endpoint: str = Field(
        "https://demo-ai-services.cognitiveservices.azure.com/",
        alias="AZURE_AI_SERVICES_ENDPOINT",
    )
    document_intelligence_endpoint: str = Field(
        "https://demo-ai-services.cognitiveservices.azure.com/",
        alias="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    )
    content_understanding_endpoint: str = Field(
        "https://demo-ai-services.cognitiveservices.azure.com/",
        alias="AZURE_CONTENT_UNDERSTANDING_ENDPOINT",
    )

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


class AzureStorageSettings(BaseSettings):
    account_name: str = Field("epcstorage", alias="AZURE_STORAGE_ACCOUNT_NAME")
    raw_container: str = Field("raw", alias="AZURE_STORAGE_RAW_CONTAINER")
    curated_container: str = Field("curated", alias="AZURE_STORAGE_CURATED_CONTAINER")
    enriched_container: str = Field("enriched", alias="AZURE_STORAGE_ENRICHED_CONTAINER")

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}

    @property
    def blob_account_url(self) -> str:
        return f"https://{self.account_name}.blob.core.windows.net"


class AzureServiceBusSettings(BaseSettings):
    namespace: str = Field(
        "epc-dev.servicebus.windows.net",
        alias="AZURE_SERVICEBUS_NAMESPACE",
    )
    ingest_queue: str = Field("document-ingest", alias="AZURE_SERVICEBUS_INGEST_QUEUE")
    enrich_queue: str = Field("document-enrich", alias="AZURE_SERVICEBUS_ENRICH_QUEUE")

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


class ContainerAppsSettings(BaseSettings):
    environment_name: str = Field("cae-epc-dev", alias="AZURE_CONTAINERAPPS_ENVIRONMENT")
    app_name: str = Field("ca-epc-api-dev", alias="AZURE_CONTAINERAPPS_APP_NAME")

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


class AppSettings(BaseSettings):
    mode: str = Field("mock", alias="APP_MODE")  # "mock" | "azure"
    environment_name: str = Field("dev", alias="APP_ENVIRONMENT")
    location: str = Field("centralus", alias="AZURE_LOCATION")
    identity: AzureIdentitySettings = AzureIdentitySettings()
    openai: AzureOpenAISettings = AzureOpenAISettings()
    postgres: AzurePostgreSQLSettings = AzurePostgreSQLSettings()
    search: AzureSearchSettings = AzureSearchSettings()
    ai_services: AzureAIServicesSettings = AzureAIServicesSettings()
    storage: AzureStorageSettings = AzureStorageSettings()
    service_bus: AzureServiceBusSettings = AzureServiceBusSettings()
    container_apps: ContainerAppsSettings = ContainerAppsSettings()

    @property
    def is_mock(self) -> bool:
        return self.mode == "mock"

    @property
    def is_azure(self) -> bool:
        return self.mode == "azure"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = AppSettings()
