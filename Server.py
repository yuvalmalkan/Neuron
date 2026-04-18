__author__ = "Yuval Malkan"


import socket
from Constants import *
import threading
import logging
import json
from UserDatabase import UserDatabase
from Pages.logic.SignupLogic import handle_signup
from Pages.logic.LoginLogic import handle_login


# Global database instance (shared across all threads)
user_db = UserDatabase('Databases/users.pkl')






def main():

    server = socket.socket()

    try:
        server.bind((serverIp, port))
        server.listen(5)
        logging.debug(f"server listening on {serverIp}:{port}")

    except Exception as e:
        logging.debug(e)
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
            logging.debug(f"server error: {e}")
            #server.close()




def handle_client(client, userId):
    """
    Handle individual client connections.
    
    Receives commands from client and processes them:
    - CMD_SIGNUP: Handle user registration
    - CMD_LOGIN: Handle user login
    - Other commands: Can be extended in future
    """
    try:
        while True:
            # Receive data from client (assuming JSON format with command and data)
            data = client.recv(4096)
            
            if not data:
                logging.debug(f"Client {userId} disconnected")
                break
            
            try:
                # Parse incoming JSON request
                request = json.loads(data.decode('utf-8'))
                command = request.get('command')
                
                response = None
                
                # Handle SIGNUP command
                if command == CMD_SIGNUP:
                    username = request.get('username')
                    email = request.get('email')
                    password = request.get('password')
                    
                    if not all([username, email, password]):
                        response = {'status': 'error', 'code': RESP_ERROR, 'message': 'Missing signup fields'}
                    else:
                        success, resp_code, user = handle_signup(username, email, password, user_db)
                        response = {
                            'status': 'success' if success else 'error',
                            'code': resp_code,
                            'user_id': user.unique_id if user else None
                        }
                
                # Handle LOGIN command
                elif command == CMD_LOGIN:
                    username = request.get('username')
                    password = request.get('password')
                    
                    if not all([username, password]):
                        response = {'status': 'error', 'code': RESP_ERROR, 'message': 'Missing login fields'}
                    else:
                        success, resp_code, user = handle_login(username, password, user_db)
                        response = {
                            'status': 'success' if success else 'error',
                            'code': resp_code,
                            'user_id': user.unique_id if user else None
                        }
                
                # Handle EXIT command
                elif command == CMD_EXIT:
                    response = {'status': 'success', 'code': 'EXIT'}
                    client.send(json.dumps(response).encode('utf-8'))
                    break
                
                else:
                    response = {'status': 'error', 'code': RESP_ERROR, 'message': f'Unknown command: {command}'}
                
                # Send response to client
                if response:
                    client.send(json.dumps(response).encode('utf-8'))
            
            except json.JSONDecodeError:
                error_response = {'status': 'error', 'code': RESP_ERROR, 'message': 'Invalid JSON format'}
                client.send(json.dumps(error_response).encode('utf-8'))
            
            except Exception as e:
                logging.error(f"Error processing request from client {userId}: {e}")
                error_response = {'status': 'error', 'code': RESP_ERROR, 'message': str(e)}
                client.send(json.dumps(error_response).encode('utf-8'))
    
    except Exception as e:
        logging.error(f"Error in handle_client for user {userId}: {e}")
    
    finally:
        try:
            client.close()
        except:
            pass
        logging.debug(f"Client {userId} connection closed")



if __name__ == '__main__':
    main()