# Client.py
__author__ = "Yuval Malkan"

import socket
import json
import logging
import sys
from tcp_by_size import send_one_message, recv_one_message
from Constants import (
    CMD_LOGIN, CMD_SIGNUP, CMD_EXIT,
    port, serverIp
)
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from Pages.ui.uiConstants import (
    load_application_font, load_stylesheet,
    WINDOW_BG, TEXT_TITLE, CARD_BG, SIDEBAR_BG, INPUT_FOCUS
)
from Pages.ui.Login import Login

# Global socket connection
_socket = None
_is_connected = False


def connect_to_server(host=serverIp, port_num=port):
    """
    Connect to the server.

    Returns:
        bool: True if connection successful, False otherwise
    """
    global _socket, _is_connected

    try:
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((host, port_num))
        _is_connected = True
        logging.info(f"Connected to server at {host}:{port_num}")
        return True
    except Exception as e:
        logging.error(f"Failed to connect to server: {e}")
        _is_connected = False
        return False


def send_request(command, **data):
    """Send a request to the server."""
    global _socket, _is_connected

    if not _is_connected:
        raise ConnectionError("Not connected to server")

    request = {"command": command, **data}
    try:
        send_one_message(_socket, json.dumps(request))
        logging.debug(f"Sent request: {command}")
    except Exception as e:
        logging.error(f"Failed to send request: {e}")
        _is_connected = False
        raise


def receive_response():
    """Receive a response from the server."""
    global _socket, _is_connected

    if not _is_connected:
        raise ConnectionError("Not connected to server")

    try:
        response_data = recv_one_message(_socket, return_type="string")
        if not response_data:
            raise ConnectionError("Server disconnected")

        response = json.loads(response_data)
        logging.debug(f"Received response: {response.get('status')}")
        return response
    except Exception as e:
        logging.error(f"Failed to receive response: {e}")
        _is_connected = False
        raise


def request_response(command, **data):
    """Send a request and wait for response in one call."""
    send_request(command, **data)
    return receive_response()


def login(username, password):
    """Send login request to server."""
    return request_response(
        CMD_LOGIN,
        username=username,
        password=password
    )


def signup(username, email, password):
    """Send signup request to server."""
    return request_response(
        CMD_SIGNUP,
        username=username,
        email=email,
        password=password
    )


def disconnect():
    """Disconnect from the server."""
    global _socket, _is_connected

    try:
        if _is_connected:
            send_request(CMD_EXIT)
    except:
        pass
    finally:
        if _socket:
            try:
                _socket.close()
            except:
                pass
        _is_connected = False
        logging.info("Disconnected from server")


def is_connected():
    """Check if connected to server."""
    return _is_connected


def main():
    """Initialize and run the Neuron client GUI."""
    app = QApplication(sys.argv)

    load_application_font()
    app.setStyle("Fusion")

    stylesheet = load_stylesheet("main")
    if stylesheet:
        app.setStyleSheet(stylesheet)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(WINDOW_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_TITLE))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SIDEBAR_BG))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(INPUT_FOCUS))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(WINDOW_BG))
    app.setPalette(palette)

    # Start with Login page
    window = Login()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
