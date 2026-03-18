__author__ = "Yuval Malkan"

import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, ec, rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from argon2 import low_level, PasswordHasher
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding





#DiffieHellman
def generate_dh_parameters(generator=2, key_size=2048):
    return dh.generate_parameters(generator=generator, key_size=key_size)

def generate_dh_keypair(parameters):
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key()
    return private_key, public_key

def dh_exchange(private_key, peer_public_key):
    return private_key.exchange(peer_public_key)


def generate_ecc_keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key



def ecc_exchange(private_key, peer_public_key):
    return private_key.exchange(ec.ECDH(), peer_public_key)


def derive_key_hkdf(shared_key, length=32, info=b'handshake data'):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    )
    return hkdf.derive(shared_key)



def derive_key_pbkdf2(password: bytes, salt: bytes, length=32, iterations=480000):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password)


def derive_key_argon2(password: bytes, salt: bytes, hash_len=32):
    derived_key = low_level.hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=hash_len,
        type=low_level.Type.ID
    )
    return derived_key



def hash_password_argon2(password: str):
    ph = PasswordHasher()
    return ph.hash(password)



def verify_password_argon2(hash_str: str, password: str):
    ph = PasswordHasher()
    try:
        ph.verify(hash_str, password)
        return True

    except Exception:
        return False



#rsa
def generate_rsa_keypair(key_size=2048):
    private_key = rsa.generate_private_key(public_exponent=65537,key_size=key_size,)
    public_key = private_key.public_key()
    return private_key, public_key



def save_rsa_keys(private_key, public_key, private_key_password: bytes, priv_filename='private_key.pem', pub_filename='public_key.pem'):

    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(private_key_password)
    )


    with open(priv_filename, 'wb') as f:
        f.write(pem_private)


    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


    with open(pub_filename, 'wb') as f:
        f.write(pem_public)

def load_rsa_keys(private_key_password: bytes, priv_filename='private_key.pem', pub_filename='public_key.pem'):
    with open(priv_filename, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=private_key_password,
            backend=default_backend()
        )

    with open(pub_filename, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read(),backend=default_backend())

    return private_key, public_key

def rsaEncrypt(public_key, message: bytes):
    encrypted_message = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_message

def rsaDecrypt(private_key, encrypted_message: bytes):
    try:
        message = private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return message

    except ValueError:
        return b"Decryption failed: Key incorrect"






#AES
def generateAES():
    key = os.urandom(32)
    iv = os.urandom(16)
    return key, iv


def aesEncrypt(key: bytes, iv: bytes, plaintext: str) -> bytes:
    plaintext_bytes = plaintext.encode('utf-8')

    padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext_bytes) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext


def aesDecrypt(key: bytes, iv: bytes, ciphertext: bytes) -> str:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext_bytes = unpadder.update(padded_data) + unpadder.finalize()

    return plaintext_bytes.decode('utf-8')