# -*- coding: utf-8 -*

import threading
import datetime
import socket
import enum
import time
import sys

class CSocket:
    def __init__(self, port: int = None):
        self.__socket_lock: threading.RLock = threading.RLock()

        self.__socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if port is not None:
            self.__socket.bind(('localhost', port))

    @property
    def socket(self) -> socket.socket:
        with self.__socket_lock:
            return self.__socket

    def set_timeout(self, seconds: int):
        self.socket.settimeout(seconds)

    def unset_timeout(self):
        self.socket.settimeout(None)


class User:
    def __init__(self, name: str, port: int):
        self.__lock: threading.RLock = threading.RLock()

        self.__name: str = name
        self.__port: int = port

        self.__last_datetime_update: datetime.datetime = datetime.datetime.now()

    @property
    def name(self) -> str:
        with self.__lock:
            return self.__name

    @property
    def port(self) -> int:
        with self.__lock:
            return self.__port

    @property
    def last_datetime_update(self) -> datetime.datetime:
        with self.__lock:
            return self.__last_datetime_update

    def update_last_datetime_update(self):
        with self.__lock:
            self.__last_datetime_update = datetime.datetime.now()


########

def listen(csocket: CSocket):
    while True:
        data = csocket.socket.recvfrom(100000)

        message = data[0].decode()
        address = data[1][1]

        from_name = message.split("|")[0]
        message_text = message.split("|")[2]

        template = "Received message from {} ({})\n" \
                   "START\n" \
                   "{}\n" \
                   "END\n" \
                   "\n".format(from_name,
                               int(address) + 1,
                               message_text)

        print(template)

        time.sleep(0.1)


def operate(csocket: CSocket):
    while True:
        input_data = input()

        raw_command = input_data.split("|")[0]

        if raw_command == "get_users":
            template = "{}|{}|{}".format(name, "get_users", "ok")

            csocket.socket.sendto(template.encode(), ("localhost", server_port))

            data = csocket.socket.recvfrom(100000)

            message = data[0].decode().split("|")[2]

            for user in message.split(","):
                print(user)

        elif raw_command == "message":
            user_port = input('Send to: ')
            message_text = input('Message body: ')

            template = "{}|{}|{}".format(name, "message", message_text)
            csocket.socket.sendto(template.encode(), ("localhost", int(user_port)))

    time.sleep(0.1)


def server_update(csocket: CSocket):
    while True:
        template = "{}|{}|{}".format(name, "launched", "ok")

        csocket.socket.sendto(template.encode(), ("localhost", server_port))

        try:
            data = csocket.socket.recvfrom(100000)

        except socket.timeout:
            pass

        time.sleep(0.5)

########

users = []
listening_socket: CSocket = None
server_update_socket: CSocket = None
operation_socket: CSocket = None

client_port: int = None
server_port: int = None
name: str = None


def main():
    global name
    global server_port
    global client_port

    global operation_socket
    global server_update_socket
    global listening_socket

    server_port = int(input('Server Port: '))
    client_port = int(input('Your Port: '))
    name = input('Your name: ')

    server_update_socket = CSocket(client_port)
    server_update_socket.set_timeout(3)

    template = "{}|{}|{}".format(name, "launched", "ok")

    server_update_socket.socket.sendto(template.encode(), ("localhost", server_port))

    data = server_update_socket.socket.recvfrom(100000)

########

    operation_socket = CSocket(client_port + 1)
    operation_socket.set_timeout(3)

    listening_socket = CSocket(client_port + 2)

########

    listening_thread = threading.Thread(target=listen, args=(listening_socket,))
    listening_thread.start()

    server_update_thread = threading.Thread(target=server_update, args=(server_update_socket,))
    server_update_thread.start()

    operation_thread = threading.Thread(target=operate, args=(operation_socket,))
    operation_thread.start()

    print("Succesfully launched")


if __name__ == '__main__':
    main()
