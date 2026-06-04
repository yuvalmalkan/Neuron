__author__ = "Yuval Malkan"

import socket
from Constants import *
import threading
import logging
import json
from tcp_by_size import send_one_message, recv_one_message
from SecureProtocol import send_secure, recv_secure
from UserDatabase import UserDatabase
from Pages.logic.SignupLogic import handle_signup
from Pages.logic.LoginLogic import handle_login
import subprocess
import sys
import tempfile
import os
from cryptography.hazmat.primitives import serialization
from EncryptionManager import generate_rsa_keypair, save_rsa_keys, load_rsa_keys, rsaDecrypt

#global dictionary to map online usernames to their socket objects
#format: { "username": (client_socket, client_aes_key) }
active_connections = {}
connections_lock = threading.Lock()

root_dir = os.path.dirname(os.path.abspath(__file__))

#for subprocesses windows
root_dir_escaped = root_dir.replace("\\", "/")

def main():
    if not os.path.exists("private_key.pem") or not os.path.exists("public_key.pem"):
        logging.info("Generating new RSA keypair and saving to disk...")
        private_key, public_key = generate_rsa_keypair(key_size=2048)
        save_rsa_keys(private_key, public_key, RSA_PASSWORD)
    else:
        logging.info("Loading existing RSA keys from disk...")
        private_key, public_key = load_rsa_keys(RSA_PASSWORD)

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

            t = threading.Thread(target=handle_client, args=(clientSocket, userId, private_key, public_key))
            t.start()
            userId += 1
        except Exception as e:
            logging.error(f"Server accept error: {e}")


def handle_client(client, userId, private_key, public_key):
    #server sends public key
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    send_one_message(client, pub_bytes)

    #receive and decrypt AES key
    encrypted_aes_payload = recv_one_message(client, return_type="bytes")
    try:
        client_aes_key = rsaDecrypt(private_key, encrypted_aes_payload)
    except Exception as e:
        logging.error(f"Secure handshake failed: {e}")
        client.close()
        return

    current_username = None
    is_chat_session = False  #if this connection registered for chat

    try:
        while True:
            #secure Protocol handles all receiving and decryption
            request = recv_secure(client, client_aes_key)
            if not request:
                break

            command = request.get('command')
            response = None

            #auth
            if command == CMD_SIGNUP:
                username, email, password = request.get('username'), request.get('email'), request.get('password')
                success, resp_code, user = handle_signup(username, email, password, user_db)
                response = {'status': 'success' if success else 'error', 'code': resp_code}
                send_secure(client, client_aes_key, response)

            elif command == CMD_LOGIN:
                username, password = request.get('username'), request.get('password')
                success, resp_code, user = handle_login(username, password, user_db)
                response = {'status': 'success' if success else 'error', 'code': resp_code}
                send_secure(client, client_aes_key, response)

            #chat
            elif command == CMD_CHAT_INIT:
                current_username = request.get('username')
                is_chat_session = True  #chat session mark
                if current_username:
                    with connections_lock:
                        active_connections[current_username] = (client, client_aes_key)
                    logging.info(f"[{current_username}] registered for chat.")

            elif command == CMD_FETCH_USERS:
                with connections_lock:
                    online = list(active_connections.keys())
                send_secure(client, client_aes_key, {'type': 'ONLINE_USERS', 'users': online})

            elif command == CMD_CHAT_REQUEST:
                target = request.get('target')
                with connections_lock:
                    target_info = active_connections.get(target)

                if target_info:
                    target_sock, target_aes_key = target_info
                    send_secure(target_sock, target_aes_key, {
                        'type': 'INCOMING_REQUEST', 'sender': current_username
                    })
                else:
                    send_secure(client, client_aes_key, {
                        'type': 'ERROR', 'message': f"Target {target} is offline."
                    })

            elif command == CMD_CHAT_ACCEPT:
                target = request.get('target')
                with connections_lock:
                    target_info = active_connections.get(target)
                if target_info:
                    target_sock, target_aes_key = target_info
                    send_secure(target_sock, target_aes_key, {
                        'type': 'REQUEST_ACCEPTED', 'peer': current_username
                    })

            elif command == CMD_CHAT_DECLINE:
                target = request.get('target')
                with connections_lock:
                    target_info = active_connections.get(target)
                if target_info:
                    target_sock, target_aes_key = target_info
                    send_secure(target_sock, target_aes_key, {
                        'type': 'REQUEST_DECLINED', 'peer': current_username
                    })

            elif command == CMD_DIRECT_MSG:
                target = request.get('target')
                text = request.get('text')
                timestamp = request.get('timestamp')

                with connections_lock:
                    target_info = active_connections.get(target)

                if target_info:
                    target_sock, target_aes_key = target_info
                    send_secure(target_sock, target_aes_key, {
                        'type': 'DIRECT_MESSAGE',
                        'sender': current_username,
                        'text': text,
                        'timestamp': timestamp
                    })

            elif command == CMD_END_SESSION:
                target = request.get('target')
                with connections_lock:
                    target_info = active_connections.get(target)
                if target_info:
                    target_sock, target_aes_key = target_info
                    send_secure(target_sock, target_aes_key, {
                        'type': 'SESSION_ENDED', 'peer': current_username
                    })

            #osint
            elif command == CMD_OSINT_USCAN:
                username_target = request.get('target_username')
                logging.info(f"OSINT scan requested for: {username_target}")

                if not username_target:
                    send_secure(client, client_aes_key, {
                        'response': RESP_OSINT_ERROR,
                        'message': 'No target username provided'
                    })

                else:
                    #run scan in a separate subprocess (completely isolated)
                    def run_scan_subprocess():
                        temp_file = None
                        try:
                            #create temp file to store results
                            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                            temp_path = temp_file.name
                            temp_file.close()

                            logging.info(f"Starting OSINT subprocess for: {username_target}")

                            #run scan script as subprocess
                            result = subprocess.run(
                                [sys.executable, '-c', f'''
                            import json
                            import sys
                            import os
                            sys.path.insert(0, "{root_dir_escaped}")
                            os.chdir("{root_dir_escaped}")
                            from CoreTools.FullScans.FullUsernameSearch import search_username_complete

                            try:
                                report = search_username_complete("{username_target}")
                                result = {{"response": "ORSLT", "report": report}}
                                with open("{temp_path}", "w") as f:
                                    json.dump(result, f)
                            except Exception as e:
                                result = {{"response": "OERRS", "message": str(e)}}
                                with open("{temp_path}", "w") as f:
                                    json.dump(result, f)
                            '''],
                                capture_output=True,
                                text=True,
                                timeout=200,
                                cwd=root_dir
                            )

                            #read result from temp file
                            if os.path.exists(temp_path):
                                with open(temp_path, 'r') as f:
                                    response = json.load(f)
                                logging.info(f"OSINT subprocess completed for: {username_target}")
                                send_secure(client, client_aes_key, response)
                            else:
                                logging.error(f"OSINT temp file not created for: {username_target}")
                                send_secure(client, client_aes_key, {
                                    'response': RESP_OSINT_ERROR,
                                    'message': 'Scan failed to write results'
                                })

                        except subprocess.TimeoutExpired:
                            logging.error(f"OSINT subprocess timeout for: {username_target}")
                            send_secure(client, client_aes_key, {
                                'response': RESP_OSINT_ERROR,
                                'message': 'Scan timeout'
                            })

                        except Exception as e:
                            logging.error(f"OSINT subprocess exception: {e}")
                            try:
                                send_secure(client, client_aes_key, {
                                    'response': RESP_OSINT_ERROR,
                                    'message': str(e)
                                })
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

            elif command == CMD_OSINT_ESCAN:
                email_target = request.get('target_email')
                logging.info(f"OSINT scan requested for email: {email_target}")

                if not email_target:
                    send_secure(client, client_aes_key, {
                        'response': RESP_OSINT_ERROR,
                        'message': 'No target email provided'
                    })

                else:
                    #run scan in a separate subprocess (completely isolated)
                    def run_email_scan_subprocess():
                        temp_file = None
                        try:
                            #create temp file to store results
                            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                            temp_path = temp_file.name
                            temp_file.close()

                            logging.info(f"Starting OSINT subprocess for email: {email_target}")

                            #get the root directory for proper imports
                            root_dir = os.path.dirname(os.path.abspath(__file__))

                            #run scan script as subprocess
                            result = subprocess.run(
                                [sys.executable, '-c', f'''
import json
import sys
import os
sys.path.insert(0, "{root_dir_escaped}")
os.chdir("{root_dir_escaped}")
from CoreTools.FullScans.FullEmailSearch import search_email_complete

try:
    report = search_email_complete("{email_target}")
    result = {{"response": "ORSLT", "report": report}}
    with open("{temp_path}", "w") as f:
        json.dump(result, f)
except Exception as e:
    result = {{"response": "OERRS", "message": str(e)}}
    with open("{temp_path}", "w") as f:
        json.dump(result, f)
'''],
                                capture_output=True,
                                text=True,
                                timeout=200,
                                cwd=root_dir  # Set working directory
                            )

                            if result.stdout:
                                logging.debug(f"Subprocess stdout: {result.stdout}")
                            if result.stderr:
                                logging.warning(f"Subprocess stderr: {result.stderr}")

                            #read result from temp file
                            if os.path.exists(temp_path):
                                with open(temp_path, 'r') as f:
                                    response = json.load(f)
                                logging.info(f"OSINT subprocess completed for email: {email_target}")
                                send_secure(client, client_aes_key, response)

                            else:
                                logging.error(f"OSINT temp file not created for email: {email_target}")
                                send_secure(client, client_aes_key, {
                                    'response': RESP_OSINT_ERROR,
                                    'message': 'Scan failed to write results'
                                })

                        except subprocess.TimeoutExpired:
                            logging.error(f"OSINT subprocess timeout for email: {email_target}")
                            send_secure(client, client_aes_key, {
                                'response': RESP_OSINT_ERROR,
                                'message': 'Scan timeout'
                            })

                        except Exception as e:
                            logging.error(f"OSINT subprocess exception: {e}", exc_info=True)
                            try:
                                send_secure(client, client_aes_key, {
                                    'response': RESP_OSINT_ERROR,
                                    'message': str(e)
                                })
                            except:
                                pass

                        finally:
                            #clean up temp file
                            if temp_file and os.path.exists(temp_path):
                                try:
                                    os.unlink(temp_path)
                                except:
                                    pass

                    scan_thread = threading.Thread(target=run_email_scan_subprocess, daemon=True)
                    scan_thread.start()

            elif command == CMD_OSINT_PSCAN:
                phone_target = request.get('target_phone')
                logging.info(f"OSINT scan requested for phone: {phone_target}")

                if not phone_target:
                    send_secure(client, client_aes_key, {
                        'response': RESP_OSINT_ERROR,
                        'message': 'No target phone provided'
                    })

                else:
                    def run_phone_scan_subprocess():
                        temp_file = None
                        try:
                            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                            temp_path = temp_file.name
                            temp_file.close()

                            logging.info(f"Starting OSINT subprocess for phone: {phone_target}")

                            result = subprocess.run(
                                [sys.executable, '-c', f'''
import json
import sys
import os
sys.path.insert(0, "{root_dir_escaped}")
os.chdir("{root_dir_escaped}")
from CoreTools.FullScans.FullPhoneSearch import search_phone_complete

try:
    report = search_phone_complete("{phone_target}")
    result = {{"response": "OPLTS", "report": report}}
    with open("{temp_path}", "w") as f:
        json.dump(result, f)
except Exception as e:
    result = {{"response": "OERRS", "message": str(e)}}
    with open("{temp_path}", "w") as f:
        json.dump(result, f)
'''],
                                capture_output=True,
                                text=True,
                                timeout=200,
                                cwd=root_dir
                            )

                            if result.stdout:
                                logging.debug(f"Subprocess stdout: {result.stdout}")
                            if result.stderr:
                                logging.warning(f"Subprocess stderr: {result.stderr}")

                            if os.path.exists(temp_path):
                                with open(temp_path, 'r') as f:
                                    response = json.load(f)
                                logging.info(f"OSINT subprocess completed for phone: {phone_target}")
                                send_secure(client, client_aes_key, response)
                            else:
                                logging.error(f"OSINT temp file not created for phone: {phone_target}")
                                send_secure(client, client_aes_key, {
                                    'response': RESP_OSINT_ERROR,
                                    'message': 'Scan failed to write results'
                                })

                        except subprocess.TimeoutExpired:
                            logging.error(f"OSINT subprocess timeout for phone: {phone_target}")
                            send_secure(client, client_aes_key, {
                                'response': RESP_OSINT_ERROR,
                                'message': 'Scan timeout'
                            })

                        except Exception as e:
                            logging.error(f"OSINT subprocess exception: {e}", exc_info=True)
                            try:
                                send_secure(client, client_aes_key, {
                                    'response': RESP_OSINT_ERROR,
                                    'message': str(e)
                                })
                            except:
                                pass

                        finally:
                            if temp_file and os.path.exists(temp_path):
                                try:
                                    os.unlink(temp_path)
                                except:
                                    pass

                    scan_thread = threading.Thread(target=run_phone_scan_subprocess, daemon=True)
                    scan_thread.start()

            elif command == CMD_EXIT:
                break

    except Exception as e:
        logging.error(f"Client handler error: {e}")

    finally:
        #only unregister from active sessions if this was a chat session
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