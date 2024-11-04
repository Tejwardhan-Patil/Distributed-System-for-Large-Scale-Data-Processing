import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import hashlib

class EncryptData:
    def __init__(self, password: str):
        self.password = password.encode()
        self.backend = default_backend()
        self.salt = os.urandom(16)
        self.key = self.derive_key(self.password, self.salt)

    def derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derives a cryptographic key using PBKDF2 HMAC with SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password)

    def encrypt(self, plaintext: str) -> str:
        """Encrypts the provided plaintext using AES in CBC mode with PKCS7 padding."""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()

        padder = PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(iv + ciphertext).decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts the provided ciphertext, it's AES-CBC encrypted with PKCS7 padding."""
        ciphertext = base64.b64decode(ciphertext)
        iv = ciphertext[:16]
        actual_ciphertext = ciphertext[16:]

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()

        padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

        unpadder = PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode('utf-8')

    def hmac_sign(self, data: str) -> str:
        """Signs the data using HMAC with SHA256."""
        h = HMAC(self.key, hashes.SHA256(), backend=self.backend)
        h.update(data.encode())
        return base64.b64encode(h.finalize()).decode('utf-8')

    def hmac_verify(self, data: str, signature: str) -> bool:
        """Verifies HMAC signature."""
        h = HMAC(self.key, hashes.SHA256(), backend=self.backend)
        h.update(data.encode())
        try:
            h.verify(base64.b64decode(signature))
            return True
        except Exception:
            return False

    def derive_scrypt_key(self, password: bytes, salt: bytes) -> bytes:
        """Derives key using Scrypt KDF, more resistant to hardware attacks."""
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=self.backend
        )
        return kdf.derive(password)

def save_encrypted_data(file_path: str, data: str, password: str):
    """Encrypts and saves data to a file."""
    encryptor = EncryptData(password)
    encrypted_data = encryptor.encrypt(data)
    with open(file_path, 'w') as f:
        f.write(encrypted_data)

def load_and_decrypt_data(file_path: str, password: str) -> str:
    """Loads and decrypts data from a file."""
    with open(file_path, 'r') as f:
        encrypted_data = f.read()
    
    decryptor = EncryptData(password)
    return decryptor.decrypt(encrypted_data)

def secure_hash_sha256(data: str) -> str:
    """Hashes data using SHA-256."""
    return hashlib.sha256(data.encode()).hexdigest()

def verify_hash_sha256(data: str, hash_value: str) -> bool:
    """Verifies the SHA-256 hash."""
    return secure_hash_sha256(data) == hash_value

def encrypt_and_sign_file(file_path: str, password: str):
    """Encrypts a file and generates HMAC for verification."""
    with open(file_path, 'r') as f:
        data = f.read()
    
    encryptor = EncryptData(password)
    encrypted_data = encryptor.encrypt(data)
    signature = encryptor.hmac_sign(data)

    with open(file_path + '.enc', 'w') as f:
        f.write(encrypted_data)

    with open(file_path + '.sig', 'w') as f:
        f.write(signature)

def decrypt_and_verify_file(file_path: str, password: str) -> bool:
    """Decrypts a file and verifies its HMAC."""
    with open(file_path + '.enc', 'r') as f:
        encrypted_data = f.read()

    with open(file_path + '.sig', 'r') as f:
        signature = f.read()

    decryptor = EncryptData(password)
    decrypted_data = decryptor.decrypt(encrypted_data)

    return decryptor.hmac_verify(decrypted_data, signature)

def main():
    password = "strongpassword"

    # Save encrypted data
    save_encrypted_data("encrypted_data.txt", "Sensitive Information", password)

    # Load and decrypt data
    decrypted_data = load_and_decrypt_data("encrypted_data.txt", password)
    print(f"Decrypted data: {decrypted_data}")

    # Secure hash and verify
    data = "Important Data"
    hash_value = secure_hash_sha256(data)
    print(f"Hash value: {hash_value}")
    verification = verify_hash_sha256(data, hash_value)
    print(f"Hash verification: {verification}")

    # Encrypt and sign file
    encrypt_and_sign_file("testfile.txt", password)

    # Decrypt and verify file
    verification_result = decrypt_and_verify_file("testfile.txt", password)
    print(f"File HMAC verification: {verification_result}")

if __name__ == "__main__":
    main()