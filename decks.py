import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend

class Deck:

    def encrypt_deck(data: bytes, key: bytes):
        iv = os.urandom(16)
        a = algorithms.AES(key)
        cipher = Cipher(a, modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        return iv + encryptor.update(padded) + encryptor.finalize()


    def decrypt_deck(ciphertext: bytes, key: bytes):
        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()


    def gen_key():
        return os.urandom(16)  
