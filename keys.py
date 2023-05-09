from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from decks import*

class Key:


    def gen_key_pair(size=2048):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=size, backend=default_backend())

        public_key = private_key.public_key()

        return private_key, public_key