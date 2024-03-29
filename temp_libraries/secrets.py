from base58 import b58encode
from did_peer_2 import KeySpec, generate
from nacl.signing import SigningKey
import logging
import json
from typing import Dict, Any


logger = logging.getLogger(__name__)

MULTIBASE_BASE58BTC = "z"

# 1110 1101  == ed
# VarInt(ed) == 1110 1101 0000 0001
# VarInt(ed) == 0000 0001 0000 0000
MULTICODEC_ED25519_PUB = b"\xed\x01"
MULTICODEC_X25519_PUB = b"\xec\x01"
MULTICODEC_ED25519_PRIV = b"\x13\x00"
MULTICODEC_X25519_PRIV = b"\x13\x02"
MULTICODEC_ED25519_PRIV = b"\x80&"
MULTICODEC_X25519_PRIV = b"\x82&"


class SecretsManager:
    """SecretsManager.
    """

    def __init__(self, storage_file: str | None = None):
        """__init__.

        Args:
            storage_file (str | None): storage_file
        """
        self.file = storage_file or "secrets.json"

    def load_secrets(self) -> Dict[str, Any] | None:
        """Load secrets from a JSON file (INSECURE!!!).

        Args:

        Returns:
            Dict[str, Any] | None:
        """
        try:
            file = open(self.file, "rb")
            config = json.loads(file.read())
            return config
        except Exception:
            logger.debug("Secrets file doesn't exist")
            return None

    def store_secrets(self, secrets: Dict[str, Any]):
        """Store secrets into a JSON file (INSECURE!!!).

        Args:
            secrets (Dict[str, Any]): secrets
        """
        try:
            file = open(self.file, "wb+")
            file.write(json.dumps(secrets).encode())
        except Exception as err:
            logger.debug("Failed to write secrets file")
            logger.exception(err)

    def generate_secrets(self) -> Dict[str, Any]:
        """Generate DID & relevant secrets.

        Args:

        Returns:
            Dict[str, Any]:
        """

        # ED25519 - For authentication
        priv_key = SigningKey.generate()
        pub_key = priv_key.verify_key

        # X25519 - For encryption
        x_priv_key = SigningKey.generate().to_curve25519_private_key()
        x_pub_key = x_priv_key.public_key

        pub_key_multi = (
            MULTIBASE_BASE58BTC
            + b58encode(MULTICODEC_ED25519_PUB + pub_key.encode()).decode()
        )
        x_pub_key_multi = (
            MULTIBASE_BASE58BTC
            + b58encode(MULTICODEC_X25519_PUB + x_pub_key.encode()).decode()
        )
        priv_key_multi = (
            MULTIBASE_BASE58BTC
            + b58encode(MULTICODEC_ED25519_PRIV + priv_key.encode()).decode()
        )
        x_priv_key_multi = (
            MULTIBASE_BASE58BTC
            + b58encode(MULTICODEC_X25519_PRIV + x_priv_key.encode()).decode()
        )

        did = generate(
            [KeySpec.encryption(x_pub_key_multi), KeySpec.verification(pub_key_multi)],
            [
                {
                    "type": "DIDCommMessaging",
                    "accept": ["didcomm/v2"],
                    "serviceEndpoint": "",
                }
            ],
        )
        secrets = {
            "ed25519": {
                "public": pub_key_multi,
                "private": priv_key_multi,
            },
            "x25519": {
                "public": x_pub_key_multi,
                "private": x_priv_key_multi,
            },
            "did": did,
        }

        return secrets

    def generate_and_save(self) -> Dict[str, Any]:
        """Generate and save secrets.

        Args:

        Returns:
            Dict[str, Any]:
        """
        secrets = self.generate_secrets()
        self.store_secrets(secrets)
        return secrets
