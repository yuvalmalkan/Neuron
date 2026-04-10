__author__ = "Yuval Malkan"


import socket
from Constants import *
import time
import threading






def main():

    server = socket.socket()

    try:
        server.bind((serverIp, port))
        server.listen(5)
        print(f"server listening on {serverIp}:{port}")

    except Exception as e:
        print(e)
        return

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    userId = 1
    while True:
        try:
            clientSocket, addr = server.accept()
            print(f"New connection from {addr}")

            t = threading.Thread(target=handle_client, args=(clientSocket, userId))
            t.start()
            userId += 1

        except Exception as e:
            print(f"server error: {e}")
            #server.close()




def handle_client(client, userId):
    pass



if __name__ == '__main__':
    main()