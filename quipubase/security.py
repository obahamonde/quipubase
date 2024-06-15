from functools import cached_property, lru_cache, wraps
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    OAuth2,
    OAuth2AuthorizationCodeBearer,
    OAuth2PasswordRequestFormStrict,
    OpenIdConnect,
    SecurityScopes,
    APIKeyCookie,
    APIKeyHeader,
)
from fastapi import Depends, HTTPException, status


def get_oidc(url: str):
    return OpenIdConnect(openIdConnectUrl=url, scheme_name="oidc")
