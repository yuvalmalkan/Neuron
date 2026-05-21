__author__ = "Yuval Malkan"

import socket
import json
import logging
import sys
import threading
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

# Global socket connections
ClientSocket = None
is_connected = False
OsintSocket = None
osint_connected = False
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


def connect_osint_socket(host=serverIp, port_num=port):
    """Create a separate socket connection for OSINT operations."""
    global OsintSocket, osint_connected

    try:
        OsintSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        OsintSocket.connect((host, port_num))
        osint_connected = True
        logging.info(f"OSINT socket connected to {host}:{port_num}")
        return True
    except Exception as e:
        logging.error(f"Failed to connect OSINT socket: {e}")
        osint_connected = False
        OsintSocket = None
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


def receive_response():
    """Receive a response from the server."""
    global ClientSocket, is_connected

    if not is_connected:
        raise ConnectionError("Not connected to server")

    try:
        response_data = recv_one_message(ClientSocket, return_type="string")
        if not response_data:
            raise ConnectionError("Server disconnected")

        response = json.loads(response_data)
        logging.debug(f"Received response: {response.get('response', response.get('status'))}")
        return response
    except Exception as e:
        logging.error(f"Failed to receive response: {e}")
        is_connected = False
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
    """Send username OSINT scan request to server via OSINT socket."""
    from Constants import CMD_OSINT_USCAN
    import time

    global OsintSocket, osint_connected

    # Always close old socket and create a fresh one for each scan
    close_osint_socket()
    time.sleep(0.1)  # Allow socket cleanup

    logging.info("Creating fresh OSINT socket for new scan...")
    if not connect_osint_socket():
        raise ConnectionError("Cannot connect OSINT socket to server")

    request = {"command": CMD_OSINT_USCAN, "target_username": username}
    try:
        send_one_message(OsintSocket, json.dumps(request))
        logging.info(f"Sent OSINT scan request for: {username}")
    except Exception as e:
        logging.error(f"Failed to send OSINT request: {e}")
        osint_connected = False
        OsintSocket = None
        raise


def receive_osint_response(timeout=180):
    """Receive OSINT response from dedicated OSINT socket."""
    global OsintSocket, osint_connected

    if not osint_connected or OsintSocket is None:
        raise ConnectionError("OSINT socket not connected")

    try:
        OsintSocket.settimeout(timeout)
        response_data = recv_one_message(OsintSocket, return_type="string")
        if not response_data:
            raise ConnectionError("OSINT socket disconnected")

        response = json.loads(response_data)
        logging.debug(f"Received OSINT response: {response.get('response')}")
        return response
    except socket.timeout:
        logging.error(f"OSINT socket timeout after {timeout}s")
        raise TimeoutError(f"No OSINT response after {timeout}s")
    except Exception as e:
        logging.error(f"Failed to receive OSINT response: {e}")
        raise
    finally:
        # Close socket after receiving response
        close_osint_socket()



def close_osint_socket():
    """Close the OSINT socket cleanly."""
    global OsintSocket, osint_connected

    try:
        if OsintSocket:
            OsintSocket.close()
            logging.info("OSINT socket closed")
    except:
        pass
    finally:
        OsintSocket = None
        osint_connected = False


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