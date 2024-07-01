# auth.py
from fastapi import APIRouter, Request, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware


def create_auth():

    config = Config(".env")
    oauth = OAuth(config)
    oauth.register(
        name="google",
        client_id=config("GOOGLE_CLIENT_ID"),
        client_secret=config("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    oauth.register(
        name="github",
        client_id=config("GITHUB_CLIENT_ID"),
        client_secret=config("GITHUB_CLIENT_SECRET"),
        authorize_url="https://github.com/login/oauth/authorize",
        authorize_params=None,
        access_token_url="https://github.com/login/oauth/access_token",
        access_token_params=None,
        refresh_token_url=None,
        client_kwargs={"scope": "user:email"},
    )

    router = APIRouter(tags=["Auth"])

    @router.get("/auth")
    async def auth(request: Request):
        provider = "google"
        redirect_uri = request.url_for("auth_callback", provider=provider)
        return await oauth.create_client(provider).authorize_redirect(
            request, redirect_uri
        )

    @router.get("/auth/{provider}")
    async def auth_callback(request: Request, provider: str):
        token = await oauth.create_client(provider).authorize_access_token(request)
        user = (
            await oauth.create_client(provider).parse_id_token(request, token)
            if provider == "google"
            else token
        )
        return {"user": user}

    return router
