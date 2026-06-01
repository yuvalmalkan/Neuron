__author__ = "Yuval Malkan"

import socket
import json
import logging
import sys
import threading
from tcp_by_size import send_one_message, recv_one_message
from Constants import (
    CMD_LOGIN, CMD_SIGNUP, CMD_EXIT,
    port, serverIp as _default_serverIp
)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from Pages.ui.uiConstants import (
    load_application_font, load_stylesheet,
    WINDOW_BG, TEXT_TITLE, CARD_BG, SIDEBAR_BG, INPUT_FOCUS
)
import sys as _sys

serverIp = _sys.argv[1] if len(_sys.argv) > 1 else _default_serverIp


#global socket connections
ClientSocket = None
is_connected = False
OsintSocket = None
osint_connected = False
socket_lock = threading.Lock()


def connect_to_server(host=serverIp, port_num=port):
    """connect to the server"""
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
    """create a separate socket connection for osint operations."""
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
    """send a request to the server."""
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
    """receive a response from the server."""
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
    """send a request and wait for response in one call"""
    send_request(command, **data)
    return receive_response()


def login(username, password):
    """send login request to server"""
    return request_response(
        CMD_LOGIN,
        username=username,
        password=password
    )


def signup(username, email, password):
    """send signup request to server"""
    return request_response(
        CMD_SIGNUP,
        username=username,
        email=email,
        password=password
    )


def disconnect():
    """disconnect from the server"""
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
    """check if connected to server"""
    return is_connected


def osint_username_scan(username: str):
    """send username OSINT scan request to server via OSINT socket."""
    from Constants import CMD_OSINT_USCAN
    import time

    global OsintSocket, osint_connected

    #always close old socket and create a fresh one for each scan
    close_osint_socket()
    time.sleep(0.1)  #socket cleanup

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




def osint_email_scan(email: str):
    """Send email OSINT scan request to server via OSINT socket."""
    from Constants import CMD_OSINT_ESCAN
    import time

    global OsintSocket, osint_connected

    #always close old socket and create a fresh one for each scan
    close_osint_socket()
    time.sleep(0.1) #socket cleanup

    logging.info("Creating fresh OSINT socket for new email scan...")
    if not connect_osint_socket():
        raise ConnectionError("Cannot connect OSINT socket to server")


    request = {"command": CMD_OSINT_ESCAN, "target_email": email}


    try:
        send_one_message(OsintSocket, json.dumps(request))
        logging.info(f"Sent OSINT email scan request for: {email}")
    except Exception as e:
        logging.error(f"Failed to send OSINT email request: {e}")
        osint_connected = False
        OsintSocket = None
        raise


def osint_phone_scan(phone: str):
    """send phone osint scan request to server via OSINT socket."""
    from Constants import CMD_OSINT_PSCAN
    import time

    global OsintSocket, osint_connected

    #always close old socket and create a fresh one for each scan
    close_osint_socket()
    time.sleep(0.1)  #allow socket cleanup

    logging.info("Creating fresh OSINT socket for new phone scan...")
    if not connect_osint_socket():
        raise ConnectionError("Cannot connect OSINT socket to server")

    request = {"command": CMD_OSINT_PSCAN, "target_phone": phone}
    try:
        send_one_message(OsintSocket, json.dumps(request))
        logging.info(f"Sent OSINT phone scan request for: {phone}")
    except Exception as e:
        logging.error(f"Failed to send OSINT phone request: {e}")
        osint_connected = False
        OsintSocket = None
        raise


def osint_raw_scan(command: str, payload: dict) -> socket.socket:
    """
    open a fresh independent socket, send one osint command, return the socket.
    Caller is responsible for receiving and closing it
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((serverIp, port))
    request = {"command": command, **payload}
    send_one_message(sock, json.dumps(request))
    return sock


def receive_from_socket(sock: socket.socket, timeout=180) -> dict:
    """receive one osint response from a given socket and close it"""
    try:
        sock.settimeout(timeout)
        data = recv_one_message(sock, return_type="string")
        if not data:
            raise ConnectionError("Socket disconnected")
        return json.loads(data)
    finally:
        try:
            sock.close()
        except:
            pass



def receive_osint_response(timeout=180):
    """receive osint response from dedicated osint socket."""

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
        #close socket after receiving response
        close_osint_socket()



def close_osint_socket():
    """close the osint socket cleanly"""
    global OsintSocket, osint_connected

    try:
        if OsintSocket:
            OsintSocket.close()
            logging.info("osint socket closed")
    except:
        pass
    finally:
        OsintSocket = None
        osint_connected = False




def main():
    if len(sys.argv) > 1:
        logging.info(f"Using server IP from argument: {serverIp}")
    else:
        logging.info(f"Using default server IP: {serverIp}")

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