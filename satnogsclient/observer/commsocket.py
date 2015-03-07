# -*- coding: utf-8 -*-
import socket


class Commsocket:
    """
    Handles connectivity with remote ctl demons
    Namely: rotctl and rigctl
    """
    _TCP_IP = '127.0.0.1'
    _TCP_PORT = 5005
    _BUFFER_SIZE = 2048

    _connected = False

    def __init__(self, ip=None, port=None):
        if not ip:
            self.TCP_IP = ip
        if not port:
            self.TCP_PORT = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @property
    def ip(self, new_ip=None):
        if new_ip:
            self._TCP_IP = new_ip
        return self._TCP_IP

    @property
    def port(self, new_port=None):
        if new_port:
            self._TCP_PORT = new_port
        return self._TCP_PORT

    @property
    def buffer_size(self, new_buffer_size=None):
        if new_buffer_size:
            self._BUFFER_SIZE = new_buffer_size
        return self._BUFFER_SIZE

    @property
    def is_connected(self):
        return self._connected

    def connect(self, ip=None, port=None):
        if not ip:
            ip = self._TCP_IP
        if not port:
            port = self._TCP_PORT
        try:
            self.s.connect((ip, port))
            self._connected = True
        except:
            return False
        return True

    def send(self, message):
        if not self.connected:
            self.connect()
        self.s.send(message)
        self.s.recv(self._BUFFER_SIZE)

    def disconnect(self):
        self.s.close()
        self._connected = False
