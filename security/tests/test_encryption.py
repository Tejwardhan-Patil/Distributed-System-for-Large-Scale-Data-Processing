import unittest
from security.encryption.EncryptData import encrypt_file, decrypt_file
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

class TestEncryption(unittest.TestCase):

    def setUp(self):
        self.key = get_random_bytes(16)
        self.file_to_encrypt = "test_file.txt"
        self.encrypted_file = "test_file_encrypted.txt"
        self.decrypted_file = "test_file_decrypted.txt"
        with open(self.file_to_encrypt, 'w') as f:
            f.write("This is a test file for encryption")
    
    def tearDown(self):
        if os.path.exists(self.file_to_encrypt):
            os.remove(self.file_to_encrypt)
        if os.path.exists(self.encrypted_file):
            os.remove(self.encrypted_file)
        if os.path.exists(self.decrypted_file):
            os.remove(self.decrypted_file)
    
    def test_encryption_decryption_process(self):
        """Test encryption and decryption processes."""
        encrypt_file(self.file_to_encrypt, self.encrypted_file, self.key)
        self.assertTrue(os.path.exists(self.encrypted_file), "Encryption failed, file not found.")

        decrypt_file(self.encrypted_file, self.decrypted_file, self.key)
        self.assertTrue(os.path.exists(self.decrypted_file), "Decryption failed, file not found.")

        with open(self.file_to_encrypt, 'r') as original_file:
            original_content = original_file.read()

        with open(self.decrypted_file, 'r') as decrypted_file:
            decrypted_content = decrypted_file.read()

        self.assertEqual(original_content, decrypted_content, "Decrypted content does not match the original content.")
    
    def test_invalid_key_decryption(self):
        """Test decryption with an invalid key."""
        encrypt_file(self.file_to_encrypt, self.encrypted_file, self.key)
        wrong_key = get_random_bytes(16)
        
        with self.assertRaises(ValueError):
            decrypt_file(self.encrypted_file, self.decrypted_file, wrong_key)
    
    def test_large_file_encryption_decryption(self):
        """Test encryption and decryption with a large file."""
        large_content = "A" * 10**6  # 1 MB file
        with open(self.file_to_encrypt, 'w') as f:
            f.write(large_content)

        encrypt_file(self.file_to_encrypt, self.encrypted_file, self.key)
        self.assertTrue(os.path.exists(self.encrypted_file), "Encryption of large file failed.")

        decrypt_file(self.encrypted_file, self.decrypted_file, self.key)
        with open(self.decrypted_file, 'r') as decrypted_file:
            decrypted_content = decrypted_file.read()

        self.assertEqual(large_content, decrypted_content, "Decrypted large file content does not match.")

    def test_invalid_file_encryption(self):
        """Test behavior when trying to encrypt a non-existent file."""
        non_existent_file = "non_existent.txt"
        with self.assertRaises(FileNotFoundError):
            encrypt_file(non_existent_file, self.encrypted_file, self.key)

    def test_encryption_without_write_permissions(self):
        """Test encryption with a directory lacking write permissions."""
        read_only_dir = "read_only_dir"
        os.makedirs(read_only_dir, exist_ok=True)
        os.chmod(read_only_dir, 0o444)

        encrypted_path = os.path.join(read_only_dir, "encrypted_file.txt")
        
        with self.assertRaises(PermissionError):
            encrypt_file(self.file_to_encrypt, encrypted_path, self.key)
        
        os.chmod(read_only_dir, 0o755)
        os.rmdir(read_only_dir)

    def test_decryption_without_write_permissions(self):
        """Test decryption with a directory lacking write permissions."""
        encrypt_file(self.file_to_encrypt, self.encrypted_file, self.key)
        
        read_only_dir = "read_only_dir"
        os.makedirs(read_only_dir, exist_ok=True)
        os.chmod(read_only_dir, 0o444)

        decrypted_path = os.path.join(read_only_dir, "decrypted_file.txt")
        
        with self.assertRaises(PermissionError):
            decrypt_file(self.encrypted_file, decrypted_path, self.key)
        
        os.chmod(read_only_dir, 0o755)
        os.rmdir(read_only_dir)

    def test_encryption_with_different_modes(self):
        """Test encryption using different modes (CBC, CFB, etc.)."""
        modes = [AES.MODE_CBC, AES.MODE_CFB, AES.MODE_OFB]
        
        for mode in modes:
            encrypt_file(self.file_to_encrypt, self.encrypted_file, self.key, mode)
            self.assertTrue(os.path.exists(self.encrypted_file), f"Encryption with mode {mode} failed.")
            
            decrypt_file(self.encrypted_file, self.decrypted_file, self.key, mode)
            self.assertTrue(os.path.exists(self.decrypted_file), f"Decryption with mode {mode} failed.")
            
            with open(self.file_to_encrypt, 'r') as original_file:
                original_content = original_file.read()
            with open(self.decrypted_file, 'r') as decrypted_file:
                decrypted_content = decrypted_file.read()

            self.assertEqual(original_content, decrypted_content, f"Decrypted content with mode {mode} does not match.")
    
    def test_encrypt_decrypt_different_key_sizes(self):
        """Test encryption and decryption with 128, 192, and 256-bit keys."""
        key_sizes = [16, 24, 32]  # 128-bit, 192-bit, 256-bit

        for size in key_sizes:
            key = get_random_bytes(size)
            encrypt_file(self.file_to_encrypt, self.encrypted_file, key)
            self.assertTrue(os.path.exists(self.encrypted_file), f"Encryption with {size*8}-bit key failed.")
            
            decrypt_file(self.encrypted_file, self.decrypted_file, key)
            self.assertTrue(os.path.exists(self.decrypted_file), f"Decryption with {size*8}-bit key failed.")
            
            with open(self.file_to_encrypt, 'r') as original_file:
                original_content = original_file.read()
            with open(self.decrypted_file, 'r') as decrypted_file:
                decrypted_content = decrypted_file.read()

            self.assertEqual(original_content, decrypted_content, f"Decrypted content with {size*8}-bit key does not match.")
    
    def test_encrypt_file_content_integrity(self):
        """Test the content of the encrypted file to ensure it is not in plain text."""
        encrypt_file(self.file_to_encrypt, self.encrypted_file, self.key)
        with open(self.encrypted_file, 'r') as f:
            encrypted_content = f.read()
        
        with open(self.file_to_encrypt, 'r') as f:
            original_content = f.read()

        self.assertNotEqual(original_content, encrypted_content, "Encrypted content should not match original content.")

if __name__ == '__main__':
    unittest.main()