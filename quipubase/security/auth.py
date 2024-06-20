from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from jose import jwt
from iso8601 import parse_date
from datetime import datetime
from uuid import uuid4


class RawKeyPair(BaseModel):
    private_key: bytes = Field(description="Private Key")
    public_key: bytes = Field(description="Public Key")


class KeyPair(BaseModel):
    private_key: str = Field(description="Private Key")
    public_key: str = Field(description="Public Key")


class Token(BaseModel):
    sub: str = Field(..., description="Subscription ID")
    aud: str = Field(..., description="Audience")
    iss: str = Field(..., description="Issuer")
    iat: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(), description="Issued At"
    )
    exp: datetime = Field(..., description="Expiration Time")
    jti: str = Field(default_factory=lambda: str(uuid4()), description="JWT ID")


def generate_keypair() -> KeyPair:
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
    )
    return KeyPair(private_key=private_key, public_key=public_key)


def generate_raw_keypair() -> RawKeyPair:
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    )
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )
    return RawKeyPair(private_key=private_key, public_key=public_key)


class JWTEncoder(BaseModel):
    payload: Optional[dict[str, Any]] = Field(
        default=None, description="Payload of the JWT Token"
    )
    private_key: str = Field(
        default_factory=lambda: generate_keypair().private_key,
        description="Private Key",
    )

    def sign(self) -> str:
        assert self.payload is not None, "Payload is required to sign the JWT Token"
        return jwt.encode(self.payload, self.private_key, algorithm="RS256")

    def verify(self, token: Optional[str] = None) -> dict[str, Any]:
        token = token or self.sign()
        return jwt.decode(token, self.private_key, algorithms=["RS256"])
