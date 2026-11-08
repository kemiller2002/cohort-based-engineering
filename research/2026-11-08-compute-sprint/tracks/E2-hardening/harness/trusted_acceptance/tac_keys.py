"""Ed25519 adapters for tac_core (I/O at the edges only)."""
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def generate(private_path: Path, public_path: Path) -> bytes:
    key = Ed25519PrivateKey.generate()
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
    private_path.chmod(0o600)
    public_raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    public_path.write_text(public_raw.hex() + "\n")
    return public_raw


def signer(private_path: Path):
    key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
    public_raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key.sign, public_raw


def verifier(public_hex: str):
    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex.strip()))

    def verify(signature: bytes, message: bytes) -> bool:
        try:
            key.verify(signature, message)
            return True
        except (InvalidSignature, ValueError):
            return False
    return verify, bytes.fromhex(public_hex.strip())
