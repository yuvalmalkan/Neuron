__author__ = "Yuval Malkan"

import json
import logging
from tcp_by_size import send_one_message, recv_one_message
from EncryptionManager import aesEncrypt, aesDecrypt


def send_secure(sock, aes_key: bytes, data_dict: dict):
    """
    Helper to convert dictionary to JSON, encrypt it, and send it.
    Maintains clean separation between network logic and application logic.
    """
    try:
        json_str = json.dumps(data_dict)
        encrypted_bytes = aesEncrypt(aes_key, json_str)
        send_one_message(sock, encrypted_bytes)
    except Exception as e:
        logging.error(f"Failed to securely send data: {e}")
        raise


def recv_secure(sock, aes_key: bytes, timeout=None) -> dict:
    """
    Helper to receive encrypted bytes, decrypt them, and parse the JSON back to a dictionary.
    """
    try:
        if timeout:
            sock.settimeout(timeout)

        encrypted_data = recv_one_message(sock, return_type="bytes")

        # Reset timeout back to blocking if it was changed
        if timeout:
            sock.settimeout(None)

        if not encrypted_data:
            return None

        json_str = aesDecrypt(aes_key, encrypted_data)
        return json.loads(json_str)

    except Exception as e:
        logging.error(f"Failed to securely receive data: {e}")
        raise