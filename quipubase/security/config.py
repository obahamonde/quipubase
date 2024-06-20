import json
from pydantic import BaseModel, HttpUrl, Field
from typing import List
from typing_extensions import Self
from abc import ABC, abstractmethod


class OAuthConfig(ABC):
    @classmethod
    @abstractmethod
    def from_config_file(cls) -> Self: ...


class GoogleOAuthConfig(BaseModel, OAuthConfig):
    client_id: str = Field(
        ..., description="The client ID issued to the app by Google."
    )
    project_id: str = Field(
        ..., description="The project ID associated with the OAuth client."
    )
    auth_uri: HttpUrl = Field(..., description="The authorization endpoint URI.")
    token_uri: HttpUrl = Field(..., description="The token endpoint URI.")
    auth_provider_x509_cert_url: HttpUrl = Field(
        ..., description="The URL for the provider's x509 certificate."
    )
    client_secret: str = Field(
        ..., description="The client secret issued to the app by Google."
    )
    redirect_uris: List[HttpUrl] = Field(
        ..., description="The redirect URIs registered for the app."
    )
    javascript_origins: List[HttpUrl] = Field(
        ..., description="The allowed JavaScript origins for the app."
    )

    @classmethod
    def from_config_file(cls):
        with open("google.json", "r") as file:
            config = json.load(file)
            return cls(**config)


class GithubOAuthConfig(BaseModel, OAuthConfig):
    owned_by: str = Field(..., description="Owner of the application")
    app_id: str = Field(..., description="Application ID")
    client_id: str = Field(..., description="Client ID")
    public_link: HttpUrl = Field(..., description="Public link to the GitHub app")
    client_secret: str = Field(..., description="Client secret")
    homepage_url: HttpUrl = Field(..., description="Homepage URL of the app")
    webhook_url: HttpUrl = Field(..., description="Webhook URL for the app")
    callback_url: HttpUrl = Field(..., description="Callback URL for the app")
    private_key: str = Field(..., description="Private key for the app")

    @classmethod
    def from_config_file(cls):
        with open("github.json", "r") as file:
            config = json.load(file)
            return cls(**config)
