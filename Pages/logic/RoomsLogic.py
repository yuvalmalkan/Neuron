__author__ = "Yuval Malkan"

"""
RoomsLogic.py
Backend logic for the Rooms/Chat page.
Handles async message sending, receiving, room management.
All network operations run in QThread to keep UI responsive.
"""

import json
import socket
import logging
from datetime import datetime
from typing import Optional, Callable

from PyQt6.QtCore import QThread, pyqtSignal, QObject


# ──────────────────────────────────────────
#  MESSAGE RECEIVE WORKER
# ──────────────────────────────────────────

class MessageReceiveWorker(QObject):
    """
    Listens on a socket for incoming messages.
    Emits signals when messages arrive.
    Runs in a background thread.
    """
    message_received = pyqtSignal(dict)  # {"room": str, "sender": str, "text": str, "timestamp": str}
    connection_lost = pyqtSignal(str)    # error message
    user_joined = pyqtSignal(str, str)   # room_name, username
    user_left = pyqtSignal(str, str)     # room_name, username

    def __init__(self, socket_conn: socket.socket):
        super().__init__()
        self.socket = socket_conn
        self._running = True

    def run(self):
        """Continuously listen for messages."""
        try:
            while self._running:
                try:
                    # Receive message with size prefix (4 bytes)
                    size_data = self.socket.recv(4)
                    if not size_data:
                        self.connection_lost.emit("Connection closed by server")
                        break

                    msg_size = int.from_bytes(size_data, byteorder='big')
                    msg_data = b''

                    # Receive full message
                    while len(msg_data) < msg_size:
                        chunk = self.socket.recv(min(4096, msg_size - len(msg_data)))
                        if not chunk:
                            raise ConnectionError("Connection lost while reading message")
                        msg_data += chunk

                    # Parse message
                    msg_json = json.loads(msg_data.decode('utf-8'))
                    msg_type = msg_json.get("type")

                    if msg_type == "MESSAGE":
                        self.message_received.emit({
                            "room": msg_json.get("room", ""),
                            "sender": msg_json.get("sender", ""),
                            "text": msg_json.get("text", ""),
                            "timestamp": msg_json.get("timestamp", self._get_timestamp())
                        })
                    elif msg_type == "USER_JOINED":
                        self.user_joined.emit(msg_json.get("room", ""), msg_json.get("username", ""))
                    elif msg_type == "USER_LEFT":
                        self.user_left.emit(msg_json.get("room", ""), msg_json.get("username", ""))

                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse message: {e}")
                except Exception as e:
                    logging.error(f"Error receiving message: {e}")
                    self.connection_lost.emit(str(e))
                    break

        except Exception as e:
            self.connection_lost.emit(str(e))

    def stop(self):
        """Stop listening."""
        self._running = False

    @staticmethod
    def _get_timestamp() -> str:
        return datetime.now().strftime("%H:%M")


# ──────────────────────────────────────────
#  MESSAGE SEND WORKER
# ──────────────────────────────────────────

class MessageSendWorker(QObject):
    """
    Sends a message to the server.
    Emits signal when send completes or fails.
    """
    send_complete = pyqtSignal(bool, str)  # success, message_id or error
    error = pyqtSignal(str)

    def __init__(self, socket_conn: socket.socket, room: str, text: str, sender: str):
        super().__init__()
        self.socket = socket_conn
        self.room = room
        self.text = text
        self.sender = sender

    def run(self):
        """Send message to server."""
        try:
            msg = {
                "type": "MESSAGE",
                "room": self.room,
                "text": self.text,
                "sender": self.sender,
                "timestamp": datetime.now().strftime("%H:%M")
            }

            msg_json = json.dumps(msg).encode('utf-8')
            msg_size = len(msg_json)

            # Send size prefix + message
            self.socket.sendall(msg_size.to_bytes(4, byteorder='big') + msg_json)
            self.send_complete.emit(True, f"{self.sender}_{self.room}_{datetime.now().timestamp()}")

        except Exception as e:
            logging.error(f"Error sending message: {e}")
            self.error.emit(str(e))
            self.send_complete.emit(False, str(e))


# ──────────────────────────────────────────
#  ROOM MANAGEMENT WORKER
# ──────────────────────────────────────────

class RoomManagementWorker(QObject):
    """
    Handles creating/joining/leaving rooms.
    """
    rooms_list_received = pyqtSignal(list)  # list of room dicts
    room_joined = pyqtSignal(dict)          # room info dict
    room_created = pyqtSignal(dict)         # new room info
    members_updated = pyqtSignal(list)      # list of member dicts
    error = pyqtSignal(str)

    def __init__(self, socket_conn: socket.socket):
        super().__init__()
        self.socket = socket_conn

    def fetch_rooms(self):
        """Request list of all rooms."""
        try:
            msg = {"type": "FETCH_ROOMS"}
            self._send_command(msg)
        except Exception as e:
            self.error.emit(f"Failed to fetch rooms: {e}")

    def create_room(self, room_name: str, members: list[str]):
        """Create a new room."""
        try:
            msg = {
                "type": "CREATE_ROOM",
                "name": room_name,
                "members": members
            }
            self._send_command(msg)
        except Exception as e:
            self.error.emit(f"Failed to create room: {e}")

    def join_room(self, room_name: str, username: str):
        """Join an existing room."""
        try:
            msg = {
                "type": "JOIN_ROOM",
                "room": room_name,
                "username": username
            }
            self._send_command(msg)
        except Exception as e:
            self.error.emit(f"Failed to join room: {e}")

    def leave_room(self, room_name: str, username: str):
        """Leave a room."""
        try:
            msg = {
                "type": "LEAVE_ROOM",
                "room": room_name,
                "username": username
            }
            self._send_command(msg)
        except Exception as e:
            self.error.emit(f"Failed to leave room: {e}")

    def fetch_room_members(self, room_name: str):
        """Fetch members of a specific room."""
        try:
            msg = {
                "type": "FETCH_MEMBERS",
                "room": room_name
            }
            self._send_command(msg)
        except Exception as e:
            self.error.emit(f"Failed to fetch members: {e}")

    def _send_command(self, msg: dict):
        """Send a command to server and wait for response."""
        try:
            msg_json = json.dumps(msg).encode('utf-8')
            msg_size = len(msg_json)
            self.socket.sendall(msg_size.to_bytes(4, byteorder='big') + msg_json)

            # Receive response
            size_data = self.socket.recv(4)
            if not size_data:
                self.error.emit("No response from server")
                return

            resp_size = int.from_bytes(size_data, byteorder='big')
            resp_data = b''

            while len(resp_data) < resp_size:
                chunk = self.socket.recv(min(4096, resp_size - len(resp_data)))
                if not chunk:
                    raise ConnectionError("Connection lost while reading response")
                resp_data += chunk

            response = json.loads(resp_data.decode('utf-8'))
            resp_type = response.get("type")

            if resp_type == "ROOMS_LIST":
                self.rooms_list_received.emit(response.get("rooms", []))
            elif resp_type == "ROOM_CREATED":
                self.room_created.emit(response)
            elif resp_type == "ROOM_JOINED":
                self.room_joined.emit(response)
            elif resp_type == "MEMBERS_LIST":
                self.members_updated.emit(response.get("members", []))

        except Exception as e:
            self.error.emit(f"Command error: {e}")


# ──────────────────────────────────────────
#  RECEIVE THREAD
# ──────────────────────────────────────────

class ReceiveThread(QThread):
    """Background thread for receiving messages."""
    message_received = pyqtSignal(dict)
    connection_lost = pyqtSignal(str)
    user_joined = pyqtSignal(str, str)
    user_left = pyqtSignal(str, str)

    def __init__(self, socket_conn: socket.socket):
        super().__init__()
        self.worker = MessageReceiveWorker(socket_conn)
        self.worker.message_received.connect(self.message_received.emit)
        self.worker.connection_lost.connect(self.connection_lost.emit)
        self.worker.user_joined.connect(self.user_joined.emit)
        self.worker.user_left.connect(self.user_left.emit)

    def run(self):
        self.worker.run()

    def stop(self):
        self.worker.stop()


# ──────────────────────────────────────────
#  SEND THREAD
# ──────────────────────────────────────────

class SendThread(QThread):
    """Background thread for sending messages."""
    send_complete = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, socket_conn: socket.socket, room: str, text: str, sender: str):
        super().__init__()
        self.worker = MessageSendWorker(socket_conn, room, text, sender)
        self.worker.send_complete.connect(self.send_complete.emit)
        self.worker.error.connect(self.error.emit)

    def run(self):
        self.worker.run()


# ──────────────────────────────────────────
#  ROOM MANAGEMENT THREAD
# ──────────────────────────────────────────

class RoomManagementThread(QThread):
    """Background thread for room operations."""
    rooms_list_received = pyqtSignal(list)
    room_joined = pyqtSignal(dict)
    room_created = pyqtSignal(dict)
    members_updated = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, socket_conn: socket.socket):
        super().__init__()
        self.worker = RoomManagementWorker(socket_conn)
        self.worker.rooms_list_received.connect(self.rooms_list_received.emit)
        self.worker.room_joined.connect(self.room_joined.emit)
        self.worker.room_created.connect(self.room_created.emit)
        self.worker.members_updated.connect(self.members_updated.emit)
        self.worker.error.connect(self.error.emit)
        self._current_operation = None

    def run(self):
        """Keep thread alive."""
        self.exec()

    def fetch_rooms(self):
        self.worker.fetch_rooms()

    def create_room(self, room_name: str, members: list[str]):
        self.worker.create_room(room_name, members)

    def join_room(self, room_name: str, username: str):
        self.worker.join_room(room_name, username)

    def leave_room(self, room_name: str, username: str):
        self.worker.leave_room(room_name, username)

    def fetch_room_members(self, room_name: str):
        self.worker.fetch_room_members(room_name)


# ──────────────────────────────────────────
#  MAIN CHAT BACKEND (Coordinator)
# ──────────────────────────────────────────

class ChatBackend(QObject):
    """
    Main coordinator for all chat operations.
    Manages connection, threads, and chat state.
    """
    # UI signals
    message_received = pyqtSignal(dict)         # incoming message
    message_sent = pyqtSignal(str)              # message_id
    send_error = pyqtSignal(str)                # error message
    connection_established = pyqtSignal()
    connection_lost_signal = pyqtSignal(str)    # error message
    rooms_loaded = pyqtSignal(list)             # list of room dicts
    members_updated = pyqtSignal(list)          # members of current room
    room_created = pyqtSignal(dict)             # new room info
    user_joined_room = pyqtSignal(str, str)     # room_name, username
    user_left_room = pyqtSignal(str, str)       # room_name, username

    def __init__(self, host: str = "localhost", port: int = 34401):
        super().__init__()
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.username: Optional[str] = None
        self.current_room: Optional[str] = None

        # Threads
        self._receive_thread: Optional[ReceiveThread] = None
        self._room_thread: Optional[RoomManagementThread] = None

    # ── CONNECTION ────────────────────────────────────────
    def connect(self, username: str) -> bool:
        """
        Connect to chat server.
        Returns True if successful, False otherwise.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.username = username

            logging.info(f"Connected to chat server as {username}")

            # Start receive thread
            self._receive_thread = ReceiveThread(self.socket)
            self._receive_thread.message_received.connect(self._on_message_received)
            self._receive_thread.connection_lost.connect(self._on_connection_lost)
            self._receive_thread.user_joined.connect(self.user_joined_room.emit)
            self._receive_thread.user_left.connect(self.user_left_room.emit)
            self._receive_thread.start()

            # Start room management thread
            self._room_thread = RoomManagementThread(self.socket)
            self._room_thread.rooms_list_received.connect(self.rooms_loaded.emit)
            self._room_thread.members_updated.connect(self.members_updated.emit)
            self._room_thread.room_created.connect(self.room_created.emit)
            self._room_thread.error.connect(lambda e: logging.error(f"Room op error: {e}"))
            self._room_thread.start()

            self.connection_established.emit()
            return True

        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            self.connection_lost_signal.emit(str(e))
            return False

    def disconnect(self):
        """Disconnect from server."""
        try:
            if self._receive_thread:
                self._receive_thread.stop()
                self._receive_thread.quit()
                self._receive_thread.wait()

            if self._room_thread:
                self._room_thread.quit()
                self._room_thread.wait()

            if self.socket:
                self.socket.close()

            logging.info("Disconnected from chat server")
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self.socket is not None

    # ── MESSAGING ────────────────────────────────────────
    def send_message(self, text: str, room: Optional[str] = None) -> bool:
        """
        Send a message to a room.
        If room is not specified, uses current_room.
        Returns True if send was initiated.
        """
        target_room = room or self.current_room
        if not target_room or not self.username or not self.socket:
            self.send_error.emit("Not connected or no room selected")
            return False

        if not text.strip():
            self.send_error.emit("Message cannot be empty")
            return False

        try:
            send_thread = SendThread(self.socket, target_room, text.strip(), self.username)
            send_thread.send_complete.connect(self._on_send_complete)
            send_thread.error.connect(self._on_send_error)
            send_thread.start()
            return True

        except Exception as e:
            logging.error(f"Error initiating send: {e}")
            self.send_error.emit(str(e))
            return False

    # ── ROOM MANAGEMENT ──────────────────────────────────
    def load_rooms(self):
        """Fetch list of all rooms from server."""
        if not self._room_thread:
            self.send_error.emit("Not connected to server")
            return
        self._room_thread.fetch_rooms()

    def create_room(self, room_name: str, members: list[str] = None):
        """Create a new room."""
        if not self._room_thread:
            self.send_error.emit("Not connected to server")
            return
        members = members or [self.username]
        self._room_thread.create_room(room_name, members)

    def join_room(self, room_name: str):
        """Join an existing room."""
        if not self._room_thread or not self.username:
            self.send_error.emit("Not connected to server")
            return
        self.current_room = room_name
        self._room_thread.join_room(room_name, self.username)

    def leave_room(self, room_name: str):
        """Leave a room."""
        if not self._room_thread or not self.username:
            self.send_error.emit("Not connected to server")
            return
        if self.current_room == room_name:
            self.current_room = None
        self._room_thread.leave_room(room_name, self.username)

    def fetch_room_members(self, room_name: str):
        """Fetch members of a specific room."""
        if not self._room_thread:
            self.send_error.emit("Not connected to server")
            return
        self._room_thread.fetch_room_members(room_name)

    def set_current_room(self, room_name: str):
        """Set the current active room."""
        self.current_room = room_name
        self.fetch_room_members(room_name)

    # ── SLOTS (internal) ──────────────────────────────────
    def _on_message_received(self, msg: dict):
        """Process incoming message."""
        logging.debug(f"Message received in {msg.get('room')}: {msg.get('sender')}")
        self.message_received.emit(msg)

    def _on_send_complete(self, success: bool, msg_id: str):
        """Handle message send completion."""
        if success:
            self.message_sent.emit(msg_id)
        else:
            self.send_error.emit(f"Send failed: {msg_id}")

    def _on_send_error(self, error: str):
        """Handle send error."""
        logging.error(f"Send error: {error}")
        self.send_error.emit(error)

    def _on_connection_lost(self, error: str):
        """Handle connection loss."""
        logging.error(f"Connection lost: {error}")
        self.connection_lost_signal.emit(error)
        self.disconnect()