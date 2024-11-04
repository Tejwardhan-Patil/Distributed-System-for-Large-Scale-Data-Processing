import os
import logging
from datetime import datetime
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

class AuditLogger:
    def __init__(self, log_dir='audit_logs', encryption_key=None):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.encryption_key = encryption_key
        logging.basicConfig(filename=self._get_log_file(), level=logging.INFO,
                            format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('AuditLogger initialized.')

    def _get_log_file(self):
        log_file_name = datetime.now().strftime('%Y-%m-%d_audit.log')
        return os.path.join(self.log_dir, log_file_name)

    def log_event(self, event_message):
        event_message_hashed = self._hash_event(event_message)
        logging.info(f"Event: {event_message_hashed}")
        if self.encryption_key:
            self._encrypt_log_file()

    def _hash_event(self, event_message):
        sha256 = hashlib.sha256()
        sha256.update(event_message.encode())
        return sha256.hexdigest()

    def _encrypt_log_file(self):
        log_file_path = self._get_log_file()
        with open(log_file_path, 'rb') as log_file:
            log_data = log_file.read()
        encrypted_data = self._symmetric_encrypt(log_data, self.encryption_key)
        with open(log_file_path, 'wb') as encrypted_log_file:
            encrypted_log_file.write(encrypted_data)

    def _symmetric_encrypt(self, data, key):
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        encryption_key = kdf.derive(key)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return salt + iv + encrypted

    def _symmetric_decrypt(self, encrypted_data, key):
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        encrypted = encrypted_data[32:]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        encryption_key = kdf.derive(key)
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        return unpadder.update(decrypted_padded) + unpadder.finalize()

class AuditLogVerifier:
    def __init__(self, public_key_path):
        self.public_key = self._load_public_key(public_key_path)

    def _load_public_key(self, public_key_path):
        with open(public_key_path, 'rb') as public_key_file:
            return serialization.load_pem_public_key(
                public_key_file.read(),
                backend=default_backend()
            )

    def verify_event(self, event_message, signature):
        event_message_hashed = hashlib.sha256(event_message.encode()).digest()
        try:
            self.public_key.verify(
                signature,
                event_message_hashed,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False

class AuditLogSigner:
    def __init__(self, private_key_path, passphrase=None):
        self.private_key = self._load_private_key(private_key_path, passphrase)

    def _load_private_key(self, private_key_path, passphrase):
        with open(private_key_path, 'rb') as private_key_file:
            return serialization.load_pem_private_key(
                private_key_file.read(),
                password=passphrase.encode() if passphrase else None,
                backend=default_backend()
            )

    def sign_event(self, event_message):
        event_message_hashed = hashlib.sha256(event_message.encode()).digest()
        signature = self.private_key.sign(
            event_message_hashed,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

# Usage
def main():
    # Sample audit logger with encryption
    encryption_key = b'supersecretpassword' 
    audit_logger = AuditLogger(encryption_key=encryption_key)

    # Logging an event
    event_message = "User Nate accessed the admin dashboard."
    audit_logger.log_event(event_message)

    # Sign and verify the event (keys are already generated and stored)
    signer = AuditLogSigner('private_key.pem', passphrase='privatepass')
    signature = signer.sign_event(event_message)

    verifier = AuditLogVerifier('public_key.pem')
    is_verified = verifier.verify_event(event_message, signature)
    
    print(f"Event verified: {is_verified}")

if __name__ == "__main__":
    main()