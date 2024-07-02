from typing import NamedTuple
import json
import base64
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class KeyPair(NamedTuple):
    public: str
    private: str


class Helper:
    """
    A class that provides helper functions
    """

    def img_b64_html(self, *, string: str):
        return f'<img src="{string}" style="width:100%;height:auto;">'

    def gen_b64_id(self):
        return base64.urlsafe_b64encode(uuid4().bytes).decode("utf-8").rstrip("=")

    def gen_b64_keypair(self):
        """
        Generate a base64 encoded RSA key pair
        """
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return json.dumps(
            KeyPair(
                public=base64.b64encode(public_key).decode("utf-8"),
                private=base64.b64encode(private_key).decode("utf-8"),
            )._asdict()
        )

    def validate_keypair(self, keypair: str):
        """
        Validate a base64 encoded RSA key pair
        """
        try:
            keypair = json.loads(keypair)
            serialization.load_pem_public_key(base64.b64decode(keypair["public"]), None)
            serialization.load_pem_private_key(
                base64.b64decode(keypair["private"]), None, backend=default_backend()
            )
            return True
        except Exception as e:
            print(e)
            return False
