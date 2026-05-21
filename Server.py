__author__ = "Yuval Malkan"

import socket
from Constants import *
import threading
import logging
import json
from tcp_by_size import send_one_message, recv_one_message
from UserDatabase import UserDatabase
from Pages.logic.SignupLogic import handle_signup
from Pages.logic.LoginLogic import handle_login
import subprocess
import sys
import tempfile
import os

# Global dictionary to map online usernames to their socket objects
# Format: { "username": client_socket }
active_connections = {}
connections_lock = threading.Lock()


def main():
    server = socket.socket()
    try:
        server.bind((serverIp, port))
        server.listen(10)
        logging.info(f"Server listening natively on {serverIp}:{port}")
    except Exception as e:
        logging.error(f"Server bind error: {e}")
        return

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    userId = 1
    while True:
        try:
            clientSocket, addr = server.accept()
            logging.debug(f"New connection from {addr}")

            t = threading.Thread(target=handle_client, args=(clientSocket, userId))
            t.start()
            userId += 1
        except Exception as e:
            logging.error(f"Server accept error: {e}")


def handle_client(client, userId):
    current_username = None
    is_chat_session = False  # Track if this connection registered for chat

    try:
        while True:
            data = recv_one_message(client, return_type="string")
            if not data:
                break

            try:
                request = json.loads(data)
                command = request.get('command')
                response = None

                # ── AUTHENTICATION ──
                if command == CMD_SIGNUP:
                    username, email, password = request.get('username'), request.get('email'), request.get('password')
                    success, resp_code, user = handle_signup(username, email, password, user_db)
                    response = {'status': 'success' if success else 'error', 'code': resp_code}
                    send_one_message(client, json.dumps(response))

                elif command == CMD_LOGIN:
                    username, password = request.get('username'), request.get('password')
                    success, resp_code, user = handle_login(username, password, user_db)
                    response = {'status': 'success' if success else 'error', 'code': resp_code}
                    send_one_message(client, json.dumps(response))

                # ── P2P CHAT ROUTING LOGIC ──
                elif command == CMD_CHAT_INIT:
                    current_username = request.get('username')
                    is_chat_session = True  # Mark this as a chat session
                    if current_username:
                        with connections_lock:
                            active_connections[current_username] = client
                        logging.info(f"[{current_username}] registered for P2P chat.")

                elif command == CMD_FETCH_USERS:
                    with connections_lock:
                        online = list(active_connections.keys())
                    send_one_message(client, json.dumps({'type': 'ONLINE_USERS', 'users': online}))

                elif command == CMD_CHAT_REQUEST:
                    target = request.get('target')
                    with connections_lock:
                        target_sock = active_connections.get(target)

                    if target_sock:
                        send_one_message(target_sock, json.dumps({
                            'type': 'INCOMING_REQUEST', 'sender': current_username
                        }))
                    else:
                        send_one_message(client, json.dumps({
                            'type': 'ERROR', 'message': f"Target {target} is offline."
                        }))

                elif command == CMD_CHAT_ACCEPT:
                    target = request.get('target')
                    with connections_lock:
                        target_sock = active_connections.get(target)
                    if target_sock:
                        send_one_message(target_sock, json.dumps({
                            'type': 'REQUEST_ACCEPTED', 'peer': current_username
                        }))

                elif command == CMD_CHAT_DECLINE:
                    target = request.get('target')
                    with connections_lock:
                        target_sock = active_connections.get(target)
                    if target_sock:
                        send_one_message(target_sock, json.dumps({
                            'type': 'REQUEST_DECLINED', 'peer': current_username
                        }))

                elif command == CMD_DIRECT_MSG:
                    target = request.get('target')
                    text = request.get('text')
                    timestamp = request.get('timestamp')

                    with connections_lock:
                        target_sock = active_connections.get(target)

                    if target_sock:
                        send_one_message(target_sock, json.dumps({
                            'type': 'DIRECT_MESSAGE',
                            'sender': current_username,
                            'text': text,
                            'timestamp': timestamp
                        }))

                elif command == CMD_END_SESSION:
                    target = request.get('target')
                    with connections_lock:
                        target_sock = active_connections.get(target)
                    if target_sock:
                        send_one_message(target_sock, json.dumps({
                            'type': 'SESSION_ENDED', 'peer': current_username
                        }))

                # ── OSINT COMMANDS ──
                elif command == CMD_OSINT_USCAN:
                    username_target = request.get('target_username')
                    logging.info(f"OSINT scan requested for: {username_target}")

                    if not username_target:
                        send_one_message(client, json.dumps({
                            'response': RESP_OSINT_ERROR,
                            'message': 'No target username provided'
                        }))
                    else:
                        # Run scan in a separate subprocess (completely isolated)
                        def run_scan_subprocess():
                            temp_file = None
                            try:
                                # Create temp file to store results
                                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                                temp_path = temp_file.name
                                temp_file.close()

                                logging.info(f"Starting OSINT subprocess for: {username_target}")

                                # Run scan script as subprocess
                                result = subprocess.run(
                                    [sys.executable, '-c', f'''
import json
import sys
from CoreTools.FullScans.FullUsernameSearch import search_username_complete

try:
    report = search_username_complete("{username_target}")
    result = {{"response": "ORLT", "report": report}}
    with open("{temp_path}", "w") as f:
        json.dump(result, f)
except Exception as e:
    result = {{"response": "OERR", "message": str(e)}}
    with open("{temp_path}", "w") as f:
        json.dump(result, f)
'''],
                                    capture_output=True,
                                    text=True,
                                    timeout=200
                                )

                                # Read result from temp file
                                if os.path.exists(temp_path):
                                    with open(temp_path, 'r') as f:
                                        response = json.load(f)
                                    logging.info(f"OSINT subprocess completed for: {username_target}")
                                    send_one_message(client, json.dumps(response))
                                else:
                                    logging.error(f"OSINT temp file not created for: {username_target}")
                                    send_one_message(client, json.dumps({
                                        'response': RESP_OSINT_ERROR,
                                        'message': 'Scan failed to write results'
                                    }))

                            except subprocess.TimeoutExpired:
                                logging.error(f"OSINT subprocess timeout for: {username_target}")
                                send_one_message(client, json.dumps({
                                    'response': RESP_OSINT_ERROR,
                                    'message': 'Scan timeout'
                                }))
                            except Exception as e:
                                logging.error(f"OSINT subprocess exception: {e}")
                                try:
                                    send_one_message(client, json.dumps({
                                        'response': RESP_OSINT_ERROR,
                                        'message': str(e)
                                    }))
                                except:
                                    pass
                            finally:
                                # Clean up temp file
                                if temp_file and os.path.exists(temp_path):
                                    try:
                                        os.unlink(temp_path)
                                    except:
                                        pass

                        scan_thread = threading.Thread(target=run_scan_subprocess, daemon=True)
                        scan_thread.start()

                elif command == CMD_EXIT:
                    break

            except json.JSONDecodeError:
                send_one_message(client, json.dumps({'type': 'ERROR', 'message': 'Invalid JSON format'}))
            except Exception as e:
                logging.error(f"Error processing command: {e}")

    except Exception as e:
        logging.error(f"Client handler error: {e}")
    finally:
        # Only unregister from active sessions if this was a chat session
        if is_chat_session and current_username:
            with connections_lock:
                if current_username in active_connections:
                    del active_connections[current_username]
            logging.info(f"[{current_username}] disconnected.")

        try:
            client.close()
        except:
            pass


if __name__ == '__main__':
    main()