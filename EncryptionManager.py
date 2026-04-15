__author__ = "Yuval Malkan"

import os
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, ec, rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from argon2 import low_level, PasswordHasher
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from Constants import debug


def generate_dh_parameters(generator=2, key_size=2048):
    """
    Generate Diffie-Hellman parameters for key exchange.

    Args:
        generator: DH generator (typically 2 or 5)
        key_size: Key size in bits (2048 or higher recommended)

    Returns:
        DHParameterNumbers object containing the parameters
    """
    logging.debug(f"Generating DH parameters with key_size={key_size}")
    return dh.generate_parameters(generator=generator, key_size=key_size)


def generate_dh_keypair(parameters):
    """
    Generate DH keypair from parameters.

    Args:
        parameters: DHParameterNumbers from generate_dh_parameters()

    Returns:
        Tuple of (private_key, public_key)
    """
    logging.debug("Generating DH keypair")
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key()
    return private_key, public_key


def dh_exchange(private_key, peer_public_key):
    """
    Perform DH key exchange to derive shared secret.

    Args:
        private_key: Your DH private key
        peer_public_key: Peer's DH public key

    Returns:
        Shared secret bytes
    """
    logging.debug("Performing DH exchange")
    shared_secret = private_key.exchange(peer_public_key)
    logging.debug(f"DH exchange completed, shared secret length: {len(shared_secret)} bytes")
    return shared_secret


def generate_ecc_keypair():
    """
    Generate Elliptic Curve (SECP256R1) keypair for key exchange.

    Returns:
        Tuple of (private_key, public_key)
    """
    logging.debug("Generating ECC keypair (SECP256R1)")
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


def ecc_exchange(private_key, peer_public_key):
    """
    Perform ECC key exchange to derive shared secret.

    Args:
        private_key: Your ECC private key
        peer_public_key: Peer's ECC public key

    Returns:
        Shared secret bytes
    """
    logging.debug("Performing ECC exchange")
    shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)
    logging.debug(f"ECC exchange completed, shared secret length: {len(shared_secret)} bytes")
    return shared_secret


# ============================================================================
# KEY DERIVATION FUNCTIONS
# ============================================================================

def derive_key_hkdf(shared_key, length=32, info=b'handshake data'):
    """
    Derive cryptographic key using HKDF (HMAC-based Key Derivation Function).
    Industry standard for key expansion after key exchange.

    Args:
        shared_key: Shared secret from key exchange
        length: Desired key length in bytes (default 32 = 256 bits)
        info: Context-specific info (default: 'handshake data')

    Returns:
        Derived key bytes
    """
    logging.debug(f"Deriving key via HKDF: length={length}, info={info}")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    )
    derived_key = hkdf.derive(shared_key)
    logging.debug("HKDF key derivation completed")
    return derived_key


def derive_key_pbkdf2(password: bytes, salt: bytes, length=32, iterations=480000):
    """
    Derive key from password using PBKDF2.
    Suitable for password-based encryption.

    Args:
        password: User password as bytes
        salt: Random salt (at least 16 bytes recommended)
        length: Desired key length in bytes
        iterations: Number of iterations (480000 is OWASP 2023 recommendation)

    Returns:
        Derived key bytes
    """
    logging.debug(f"Deriving key via PBKDF2: iterations={iterations}, salt_len={len(salt)}")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    derived_key = kdf.derive(password)
    logging.debug("PBKDF2 key derivation completed")
    return derived_key


def derive_key_argon2(password: bytes, salt: bytes, hash_len=32):
    """
    Derive key from password using Argon2 (OWASP recommended).
    More resistant to GPU/ASIC attacks than PBKDF2.

    Args:
        password: User password as bytes
        salt: Random salt (16 bytes recommended)
        hash_len: Desired output length in bytes

    Returns:
        Derived key bytes
    """
    logging.debug(f"Deriving key via Argon2: salt_len={len(salt)}, hash_len={hash_len}")
    derived_key = low_level.hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=hash_len,
        type=low_level.Type.ID
    )
    logging.debug("Argon2 key derivation completed")
    return derived_key


# ============================================================================
# PASSWORD HASHING (ARGON2)
# ============================================================================

def hash_password_argon2(password: str):
    """
    Hash password using Argon2 for storage in database.
    OWASP recommended password hashing algorithm.

    Args:
        password: Plain text password

    Returns:
        Argon2 hash string (includes salt and parameters)
    """
    logging.debug("Hashing password with Argon2")
    ph = PasswordHasher()
    hash_result = ph.hash(password)
    logging.debug("Password hashing completed")
    return hash_result


def verify_password_argon2(hash_str: str, password: str):
    """
    Verify password against Argon2 hash.

    Args:
        hash_str: Hash from hash_password_argon2()
        password: Plain text password to verify

    Returns:
        Boolean: True if password matches, False otherwise
    """
    logging.debug("Verifying password with Argon2")
    ph = PasswordHasher()
    try:
        ph.verify(hash_str, password)
        logging.debug("Password verification successful")
        return True
    except Exception as e:
        logging.debug(f"Password verification failed: {e}")
        return False


# ============================================================================
# RSA ENCRYPTION (INDUSTRY STANDARD: OAEP + SHA-256)
# ============================================================================

def generate_rsa_keypair(key_size=2048):
    """
    Generate RSA keypair (industry standard: 2048-bit minimum, 4096-bit recommended).

    Args:
        key_size: RSA key size in bits (2048 minimum, 4096 preferred for long-term security)

    Returns:
        Tuple of (private_key, public_key)
    """
    if key_size < 2048:
        logging.warning(f"RSA key_size={key_size} is less than 2048 bits - not recommended!")

    logging.debug(f"Generating RSA {key_size}-bit keypair")
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Industry standard exponent
        key_size=key_size,
    )
    public_key = private_key.public_key()
    logging.debug("RSA keypair generation completed")
    return private_key, public_key


def save_rsa_keys(private_key, public_key, private_key_password: bytes,
                  priv_filename='private_key.pem', pub_filename='public_key.pem'):
    """
    Save RSA keypair to PEM files with password protection.

    Args:
        private_key: RSA private key object
        public_key: RSA public key object
        private_key_password: Password to encrypt private key
        priv_filename: Output filename for private key
        pub_filename: Output filename for public key

    Note:
        Private key is encrypted with BestAvailableEncryption (AES-256 in PKCS8 format)
        Public key is stored unencrypted
    """
    logging.info(f"Saving RSA keys: private={priv_filename}, public={pub_filename}")

    try:
        # Serialize private key with encryption
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,  # Industry standard format
            encryption_algorithm=serialization.BestAvailableEncryption(private_key_password)
        )

        with open(priv_filename, 'wb') as f:
            f.write(pem_private)
        logging.debug(f"Private key saved to {priv_filename}")

        # Serialize public key
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo  # Industry standard
        )

        with open(pub_filename, 'wb') as f:
            f.write(pem_public)
        logging.debug(f"Public key saved to {pub_filename}")

    except Exception as e:
        logging.error(f"Failed to save RSA keys: {e}")
        raise


def load_rsa_keys(private_key_password: bytes, priv_filename='private_key.pem',
                  pub_filename='public_key.pem'):
    """
    Load RSA keypair from PEM files.

    Args:
        private_key_password: Password to decrypt private key
        priv_filename: Filename of private key
        pub_filename: Filename of public key

    Returns:
        Tuple of (private_key, public_key)

    Raises:
        ValueError: If password is incorrect or file not found
    """
    logging.info(f"Loading RSA keys from: {priv_filename}, {pub_filename}")

    try:
        with open(priv_filename, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=private_key_password,
                backend=default_backend()
            )
        logging.debug(f"Private key loaded successfully")

        with open(pub_filename, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
        logging.debug(f"Public key loaded successfully")

        return private_key, public_key

    except Exception as e:
        logging.error(f"Failed to load RSA keys: {e}")
        raise


def rsaEncrypt(public_key, message: bytes):
    """
    Encrypt message using RSA with OAEP padding (industry standard).

    WARNING: Maximum message size is ~190 bytes with 2048-bit key
    For larger data, use hybrid encryption: RSA encrypt AES key, AES encrypt data.

    Args:
        public_key: RSA public key
        message: Data to encrypt (must be bytes, max ~190 bytes)

    Returns:
        Encrypted data as bytes

    Raises:
        ValueError: If message is too long
    """
    # Calculate max message size
    key_size = public_key.key_size
    max_msg_size = (key_size // 8) - 66  # OAEP overhead with SHA-256

    if len(message) > max_msg_size:
        logging.error(f"Message too long: {len(message)} > {max_msg_size} bytes")
        raise ValueError(f"Message too long ({len(message)} > {max_msg_size} bytes). Use hybrid encryption.")

    logging.debug(f"RSA encrypting {len(message)} bytes with {key_size}-bit key")

    try:
        # OAEP padding is industry standard (PKCS#1 v2.1)
        encrypted_message = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),  # MGF1 with SHA256
                algorithm=hashes.SHA256(),  # Use SHA256 for OAEP
                label=None
            )
        )
        logging.debug(f"RSA encryption successful, ciphertext size: {len(encrypted_message)} bytes")
        return encrypted_message

    except Exception as e:
        logging.error(f"RSA encryption failed: {e}")
        raise


def rsaDecrypt(private_key, encrypted_message: bytes):
    """
    Decrypt RSA-encrypted message using OAEP padding.

    Args:
        private_key: RSA private key
        encrypted_message: Encrypted data from rsaEncrypt()

    Returns:
        Decrypted message as bytes

    Raises:
        ValueError: If decryption fails (wrong key, corrupted data, etc.)
    """
    logging.debug(f"RSA decrypting {len(encrypted_message)} bytes")

    try:
        message = private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        logging.debug(f"RSA decryption successful, plaintext size: {len(message)} bytes")
        return message

    except ValueError as e:
        # Use proper exception instead of returning error message
        logging.error(f"RSA decryption failed: Invalid ciphertext or key mismatch")
        raise ValueError("RSA decryption failed: Invalid ciphertext or incorrect key") from e


# ============================================================================
# AES ENCRYPTION (AES-256-CBC WITH PKCS7 PADDING)
# ============================================================================

def generateAES():
    """
    Generate random AES-256 key and IV for encryption.

    Returns:
        Tuple of (key, iv) where:
        - key: 32 bytes for AES-256
        - iv: 16 bytes for CBC mode

    Note:
        IV should be unique for each encryption with the same key.
        Both should be transmitted securely to recipient.
    """
    logging.debug("Generating AES-256 key and IV")
    key = os.urandom(32)  # 256 bits for AES-256
    iv = os.urandom(16)  # 128 bits for CBC block size
    logging.debug(f"Generated AES key ({len(key)} bytes) and IV ({len(iv)} bytes)")
    return key, iv


def aesEncrypt(key: bytes, iv: bytes, plaintext: str) -> bytes:
    """
    Encrypt plaintext using AES-256-CBC with PKCS7 padding.

    Args:
        key: 32-byte AES-256 key
        iv: 16-byte initialization vector
        plaintext: String to encrypt

    Returns:
        Encrypted ciphertext as bytes

    Note:
        IV must be random and unique for each encryption with same key.
        IV can be transmitted in plaintext (it doesn't need to be secret).
    """
    logging.debug(f"AES encrypting {len(plaintext)} characters")

    try:
        plaintext_bytes = plaintext.encode('utf-8')

        # Apply PKCS7 padding (industry standard)
        padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext_bytes) + padder.finalize()

        # Encrypt with AES-256-CBC
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        logging.debug(f"AES encryption successful, ciphertext size: {len(ciphertext)} bytes")
        return ciphertext

    except Exception as e:
        logging.error(f"AES encryption failed: {e}")
        raise


def aesDecrypt(key: bytes, iv: bytes, ciphertext: bytes) -> str:
    """
    Decrypt AES-256-CBC encrypted message with PKCS7 padding.

    Args:
        key: Same 32-byte key used for encryption
        iv: Same 16-byte IV used for encryption
        ciphertext: Encrypted data from aesEncrypt()

    Returns:
        Decrypted plaintext as string

    Raises:
        ValueError: If decryption fails or padding is invalid
    """
    logging.debug(f"AES decrypting {len(ciphertext)} bytes")

    try:
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 padding
        unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext_bytes = unpadder.update(padded_data) + unpadder.finalize()

        plaintext = plaintext_bytes.decode('utf-8')
        logging.debug(f"AES decryption successful, plaintext size: {len(plaintext)} characters")
        return plaintext

    except Exception as e:
        logging.error(f"AES decryption failed: {e}")
        raise
