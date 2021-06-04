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
        self.__server_update_port: int = port
        self.__listening_port: int = port + 2
        self.__operate_port: int = port + 1

        self.__last_datetime_update: datetime.datetime = datetime.datetime.now()

    def __str__(self):
        return "{} {} {} {} {}".format(self.server_update_port, self.operate_port, self.listening_port, self.name,
                                       self.last_datetime_update)

    @property
    def name(self) -> str:
        with self.__lock:
            return self.__name

    @property
    def server_update_port(self) -> int:
        with self.__lock:
            return self.__server_update_port

    @property
    def listening_port(self) -> int:
        with self.__lock:
            return self.__listening_port

    @property
    def operate_port(self) -> int:
        with self.__lock:
            return self.__operate_port

    @property
    def last_datetime_update(self) -> datetime.datetime:
        with self.__lock:
            return self.__last_datetime_update

    def update_last_datetime_update(self):
        with self.__lock:
            self.__last_datetime_update = datetime.datetime.now()


def operate(csocket: CSocket):
    while True:
        data = csocket.socket.recvfrom(1024)

        message = data[0].decode()
        address = data[1][1]

        command = message.split("|")[1]

        if command == "launched":
            new_user = None

            for user in users:
                if user.server_update_port == int(address):
                    new_user = user

            if new_user is None:
                new_user = User(message.split("|")[0], int(address))
                users.append(new_user)

            else:
                user.update_last_datetime_update()

            print("UPDATED USER {}".format(new_user))

            template = "{}|{}|{}".format("server", "launched", "ok")

            csocket.socket.sendto(template.encode(), ("localhost", int(address)))

        elif command == "get_users":
            raw_users = ""

            for user in users:
                raw_users += "{}({}),".format(user.name, user.listening_port)

            template = "{}|{}|{}".format("server", "get_users", raw_users)

            csocket.socket.sendto(template.encode(), ("localhost", int(address)))

            print("GET USERS SENT TO {}".format(address))

        time.sleep(0.05)


def user_cleaning():
    while True:
        for user in users:
            if (datetime.datetime.now() - user.last_datetime_update).seconds >= 4:

                print("REMOVING USER {}".format(user))
                users.remove(user)

        time.sleep(1)

server_port: int = None
operation_socket: CSocket = None
users = []

def main():
    global users
    global server_port
    global operation_socket

    server_port = int(input('Server Port: '))

    operation_socket = CSocket(server_port)

    operate_thread = threading.Thread(target=operate, args=(operation_socket,))
    operate_thread.start()

    users_cleaning_thread = threading.Thread(target=user_cleaning)
    users_cleaning_thread.start()

    print("Succesfully launched")


if __name__ == '__main__':
    main()
