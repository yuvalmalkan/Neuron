__author__ = "Yuval Malkan"

import json
import socket
import logging
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from tcp_by_size import send_one_message, recv_one_message

from Constants import (
    CMD_CHAT_INIT, CMD_FETCH_USERS, CMD_CHAT_REQUEST,
    CMD_CHAT_ACCEPT, CMD_CHAT_DECLINE, CMD_DIRECT_MSG, CMD_END_SESSION
)


class ChatBackend(QThread):
    online_users_received = pyqtSignal(list)
    incoming_request = pyqtSignal(str)
    request_accepted = pyqtSignal(str)
    request_declined = pyqtSignal(str)
    message_received = pyqtSignal(dict)
    session_ended = pyqtSignal(str)
    connection_lost = pyqtSignal(str)

    def __init__(self, host="127.0.0.1", port=34401):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.active_peer = None
        self._is_running = False

    def connect(self, username):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.username = username

            # Register with the Server
            req = {"command": CMD_CHAT_INIT, "username": self.username}
            send_one_message(self.socket, json.dumps(req))

            # Start the background listening loop
            self._is_running = True
            self.start()
            return True

        except Exception as e:
            logging.error(f"Chat connection failed: {e}")
            return False

    def disconnect(self):
        self._is_running = False
        if self.socket:
            try:
                self.socket.close()  # Closes socket, which breaks the recv() block below cleanly
            except:
                pass

        self.wait()  # Safely waits for thread to shut down
        self.active_peer = None

    def run(self):
        """Standard listening loop running in the background thread."""
        while self._is_running:
            try:
                data = recv_one_message(self.socket, return_type="string")
                if not data:
                    break

                payload = json.loads(data)
                msg_type = payload.get("type")

                # Qt natively routes these emissions safely to the Main UI Thread
                if msg_type == "ONLINE_USERS":
                    self.online_users_received.emit(payload.get("users", []))

                elif msg_type == "INCOMING_REQUEST":
                    self.incoming_request.emit(payload.get("sender"))

                elif msg_type == "REQUEST_ACCEPTED":
                    self.active_peer = payload.get("peer")
                    self.request_accepted.emit(self.active_peer)

                elif msg_type == "REQUEST_DECLINED":
                    self.request_declined.emit(payload.get("peer"))

                elif msg_type == "DIRECT_MESSAGE":
                    self.message_received.emit(payload)

                elif msg_type == "SESSION_ENDED":
                    if self.active_peer == payload.get("peer"):
                        self.active_peer = None
                    self.session_ended.emit(payload.get("peer"))

            except Exception:
                break  # Loop breaks safely on disconnect

        if self._is_running:
            self.connection_lost.emit("Disconnected from server.")

    # ── Sending Methods (Called directly from Main UI Thread) ──
    def fetch_online_users(self):
        self._send({"command": CMD_FETCH_USERS})

    def send_chat_request(self, target):
        self._send({"command": CMD_CHAT_REQUEST, "target": target})

    def accept_chat(self, target):
        self.active_peer = target
        self._send({"command": CMD_CHAT_ACCEPT, "target": target})

    def decline_chat(self, target):
        self._send({"command": CMD_CHAT_DECLINE, "target": target})

    def send_message(self, text):
        if self.active_peer:
            self._send({
                "command": CMD_DIRECT_MSG,
                "target": self.active_peer,
                "text": text,
                "timestamp": datetime.now().strftime("%H:%M")
            })

    def end_session(self):
        if self.active_peer:
            self._send({"command": CMD_END_SESSION, "target": self.active_peer})
            self.active_peer = None

    def _send(self, data):
        if self.socket:
            try:
                send_one_message(self.socket, json.dumps(data))
            except Exception as e:
                logging.error(f"Failed to send payload: {e}")