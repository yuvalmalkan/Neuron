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
import threading

#from Pages.ui.Login import Login





# Global socket connection
ClientSocket = None
is_connected = False
socket_lock = threading.Lock()




def connect_to_server(host=serverIp, port_num=port):
    """Connect to the server."""
    global ClientSocket, is_connected

    try:
        ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ClientSocket.connect((host, port_num))
        is_connected = True
        logging.info(f"Connected to server at {host}:{port_num}")
        return True
    except Exception as e:
        logging.error(f"Failed to connect to server: {e}")
        is_connected = False
        return False





def send_request(command, **data):
    """Send a request to the server."""
    global ClientSocket, is_connected

    if not is_connected:
        raise ConnectionError("Not connected to server")

    request = {"command": command, **data}


    try:
        send_one_message(ClientSocket, json.dumps(request))
        logging.debug(f"Sent request: {command}")

    except Exception as e:
        logging.error(f"Failed to send request: {e}")
        is_connected = False
        raise




def receive_response(timeout=120):
    """Receive a response from the server with timeout."""
    global ClientSocket, is_connected

    if not is_connected:
        raise ConnectionError("Not connected to server")

    try:
        # Set socket timeout
        ClientSocket.settimeout(timeout)

        response_data = recv_one_message(ClientSocket, return_type="string")
        if not response_data:
            raise ConnectionError("Server disconnected")

        response = json.loads(response_data)
        logging.debug(f"Received response: {response.get('response', response.get('status'))}")
        return response
    except socket.timeout:
        logging.error(f"Socket timeout waiting for response after {timeout}s")
        raise TimeoutError(f"No response from server after {timeout}s")
    except Exception as e:
        logging.error(f"Failed to receive response: {e}")
        is_connected = False
        raise
    finally:
        # Reset timeout to blocking mode
        try:
            ClientSocket.settimeout(None)
        except:
            pass



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
    global ClientSocket, is_connected

    try:
        if is_connected:
            send_request(CMD_EXIT)
            is_connected = False
    except:
        pass
    finally:
        if ClientSocket:
            try:
                ClientSocket.close()
            except:
                pass
        is_connected = False
        logging.info("Disconnected from server")


def get_is_connected() -> bool:
    """Check if connected to server."""
    return is_connected





def osint_username_scan(username: str):
    """Send username OSINT scan request to server."""
    from Constants import CMD_OSINT_USCAN
    send_request(
        CMD_OSINT_USCAN,
        target_username=username
    )









def main():
    from Pages.ui.Login import Login

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

    #Login page
    window = Login()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
