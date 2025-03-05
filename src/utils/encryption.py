import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import json
import nacl.utils
from nacl.public import PrivateKey, SealedBox

class EncryptionManager:
    def __init__(self, password: str):
        self.password = password.encode()
        self.backend = default_backend()
        self.salt = os.urandom(16)
        self.kdf = Scrypt(
            salt=self.salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=self.backend
        )
        self.key = self.kdf.derive(self.password)

    def encrypt(self, data: bytes) -> bytes:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        encrypted_data = aesgcm.encrypt(nonce, data, None)
        return base64.b64encode(self.salt + nonce + encrypted_data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        encrypted_data = base64.b64decode(encrypted_data)
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=self.backend
        )
        key = kdf.derive(self.password)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

class ECDSAKeyManager:
    def __init__(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.public_key = self.private_key.public_key()

    def sign(self, data: bytes) -> bytes:
        return self.private_key.sign(data, ec.ECDSA(hashes.SHA256()))

    def verify(self, signature: bytes, data: bytes) -> bool:
        try:
            self.public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True
        except:
            return False

    def serialize_private_key(self) -> bytes:
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def serialize_public_key(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

class HSMKeyManager:
    def __init__(self):
        self.private_key = PrivateKey.generate()
        self.public_key = self.private_key.public_key

    def encrypt(self, data: bytes) -> bytes:
        sealed_box = SealedBox(self.public_key)
        return sealed_box.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        sealed_box = SealedBox(self.private_key)
        return sealed_box.decrypt(encrypted_data)

    def serialize_private_key(self) -> bytes:
        return self.private_key.encode()

    def serialize_public_key(self) -> bytes:
        return self.public_key.encode()

def save_vault(data: dict, password: str, file_path: str):
    encryption_manager = EncryptionManager(password)
    encrypted_data = encryption_manager.encrypt(json.dumps(data).encode())
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)

def load_vault(password: str, file_path: str) -> dict:
    encryption_manager = EncryptionManager(password)
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
    decrypted_data = encryption_manager.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())
