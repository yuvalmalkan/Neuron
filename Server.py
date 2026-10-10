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
import platform
from cryptography.hazmat.primitives import serialization
from EncryptionManager import generate_rsa_keypair, save_rsa_keys, load_rsa_keys, rsaDecrypt


root_dir = os.path.dirname(os.path.abspath(__file__))

#for subprocesses repr handles Windows bugs
root_dir_repr = repr(root_dir)

def _subprocess_flags() -> dict:
    #suppress console popup windows on Windows
    if platform.system() == "Windows":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}

def _safe_terminate(proc: subprocess.Popen, timeout: int = 3) -> None:
    #terminate a subprocess safely

    try:
        proc.terminate()
        proc.wait(timeout=timeout)

    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=2)
        except Exception:
            pass

    except Exception:
        pass







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

    client_lock = threading.Lock()

    active_subprocesses = []
    subprocesses_lock = threading.Lock()

    #server sends public key
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with client_lock:
        send_one_message(client, pub_bytes)

    #receive and decrypt aes key
    encrypted_aes_payload = recv_one_message(client, return_type="bytes")
    try:
        client_aes_key = rsaDecrypt(private_key, encrypted_aes_payload)

    except Exception as e:
        logging.error(f"Secure handshake failed: {e}")
        client.close()
        return

    try:
        while True:
            request = recv_secure(client, client_aes_key)
            if not request:
                break

            command = request.get('command')
            response = None

            #login/signup
            if command == CMD_SIGNUP:
                username, email, password = request.get('username'), request.get('email'), request.get('password')
                success, resp_code, user = handle_signup(username, email, password, user_db)
                response = {'status': 'success' if success else 'error', 'code': resp_code}
                with client_lock:
                    send_secure(client, client_aes_key, response)

            elif command == CMD_LOGIN:
                username, password = request.get('username'), request.get('password')
                success, resp_code, user = handle_login(username, password, user_db)
                response = {'status': 'success' if success else 'error', 'code': resp_code}
                with client_lock:
                    send_secure(client, client_aes_key, response)

            #osint
            elif command in [CMD_OSINT_USCAN, CMD_OSINT_ESCAN, CMD_OSINT_PSCAN]:

                target_value = request.get('target_username') or request.get('target_email') or request.get('target_phone')

                if not target_value:
                    with client_lock:
                        send_secure(client, client_aes_key, {
                            'response': RESP_OSINT_ERROR,
                            'message': 'No scan target provided'
                        })
                    continue

                def run_scan_generic(cmd, val):
                    proc = None
                    try:
                        #create temp for results
                        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', dir=root_dir)
                        temp_path = temp_file.name
                        temp_file.close()
                        temp_repr = repr(temp_path)

                        #what script to use
                        script_import = ""
                        if cmd == CMD_OSINT_USCAN:
                            script_import = f"from CoreTools.FullScans.FullUsernameSearch import search_username_complete; report = search_username_complete('{val}')"
                        elif cmd == CMD_OSINT_ESCAN:
                            script_import = f"from CoreTools.FullScans.FullEmailSearch import search_email_complete; report = search_email_complete('{val}')"
                        elif cmd == CMD_OSINT_PSCAN:
                            script_import = f"from CoreTools.FullScans.FullPhoneSearch import search_phone_complete; report = search_phone_complete('{val}')"


                        proc = subprocess.Popen(
                            [sys.executable, '-c', f'''
                        import json
                        import sys
                        import os
                        sys.path.insert(0, {root_dir_repr})
                        os.chdir({root_dir_repr})
                        {script_import}
                        try:
                            result = {{"response": "ORSLT" if "{cmd}" != "{CMD_OSINT_PSCAN}" else "OPLTS", "report": report}}
                            with open({temp_repr}, "w") as f:
                                json.dump(result, f)
                        except Exception as e:
                            result = {{"response": "OERRS", "message": str(e)}}
                            with open({temp_repr}, "w") as f:
                                json.dump(result, f)
                        '''],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=root_dir,
                            **_subprocess_flags()
                        )


                        with subprocesses_lock:
                            active_subprocesses.append(proc)

                        #wait for timeout
                        stdout, stderr = proc.communicate(timeout=200)


                        #read result from temp
                        if os.path.exists(temp_path):
                            with open(temp_path, 'r') as f:
                                scan_response = json.load(f)

                            with client_lock:
                                send_secure(client, client_aes_key, scan_response)

                    except subprocess.TimeoutExpired:
                        logging.error(f"OSINT subprocess timeout for target: {val}")
                        if proc:
                            _safe_terminate(proc)


                        try:
                            with client_lock:
                                send_secure(client, client_aes_key,
                                            {'response': RESP_OSINT_ERROR, 'message': 'Scan timeout'})
                        except:
                            pass

                    except Exception as e:
                        logging.error(f"OSINT subprocess exception: {e}")
                        try:
                            with client_lock:
                                send_secure(client, client_aes_key, {'response': RESP_OSINT_ERROR, 'message': str(e)})
                        except:
                            pass

                    finally:
                        #clean temp
                        if proc:
                            with subprocesses_lock:
                                if proc in active_subprocesses:
                                    active_subprocesses.remove(proc)

                        if os.path.exists(temp_path):
                            try:
                                os.unlink(temp_path)

                            except:
                                pass

                scan_thread = threading.Thread(target=run_scan_generic, args=(command, target_value), daemon=True)
                scan_thread.start()

            elif command == CMD_EXIT:
                break

    except Exception as e:
        logging.error(f"Client handler error: {e}")

    finally:
        #prevent zombie threads
        with subprocesses_lock:
            for proc in active_subprocesses:
                try:
                    logging.info(f"Terminating orphan OSINT subprocess PID: {proc.pid} due to client disconnect.")
                    _safe_terminate(proc)
                except Exception as ex:
                    logging.error(f"Failed to terminate process {proc.pid}: {ex}")
            active_subprocesses.clear()

        try:
            with client_lock:
                client.close()
        except:
            pass


if __name__ == '__main__':
    main()