"""Wallet signing and RSA operations configured outside the source tree."""

import hashlib
import os

import rsa
from django.core.exceptions import ImproperlyConfigured


class WalletCrypt:
    secret = os.environ.get('WALLET_SIGNATURE_SECRET', '').encode()
    n = int(os.environ.get('WALLET_RSA_N') or 0)
    e = int(os.environ.get('WALLET_RSA_E') or 0)

    @classmethod
    def public_numbers(cls):
        if not cls.n or not cls.e:
            raise ImproperlyConfigured('Wallet RSA public key is not configured.')
        return cls.n, cls.e

    def __init__(self):
        if not self.secret:
            raise ImproperlyConfigured('Wallet signing secret is not configured.')
        n, e = self.public_numbers()
        parts = [int(os.environ.get(name) or 0) for name in (
            'WALLET_RSA_D', 'WALLET_RSA_P', 'WALLET_RSA_Q')]
        if not all(parts):
            raise ImproperlyConfigured('Wallet RSA private key is not configured.')
        self.public_key = rsa.key.PublicKey(n, e)
        self.private_key = rsa.key.PrivateKey(n, e, *parts)

    def generate_signature(self, signature_identifier: str):
        hasher = hashlib.sha512()
        hasher.update(self.secret + str(signature_identifier).encode())
        checksum = hashlib.md5()
        checksum.update(str(signature_identifier).encode())
        final = hashlib.sha256()
        final.update((str(hasher.hexdigest()).lower() + str(checksum.hexdigest()).lower()).encode())
        return final.hexdigest()

    def validate_signature(self, signature_identifier: str, signature: str, body: str):
        true_sign = self.generate_signature(signature_identifier)
        true_side = hashlib.md5()
        true_side.update((true_sign + body).lower().encode())
        return signature.lower() == true_side.hexdigest().lower()

    def static_decrypt(self, msg: bytes) -> str:
        return rsa.decrypt(msg, self.private_key).decode()

    def static_encrypt(self, msg: str) -> bytes:
        return rsa.encrypt(msg.encode(), self.public_key)
