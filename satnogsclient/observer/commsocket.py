# -*- coding: utf-8 -*-
import logging
import socket


logger = logging.getLogger('satnogsclient')


class Commsocket:
    """
    Handles connectivity with remote ctl demons
    Namely: rotctl and rigctl
    """

    _BUFFER_SIZE = 2048
    _TASKS_BUFFER_SIZE = 10480
    _connected = False

    def __init__(self, ip, port):
        self._TCP_IP = ip
        self._TCP_PORT = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    @property
    def ip(self):
        return self._TCP_IP

    @ip.setter
    def ip(self, new_ip):
        self._TCP_IP = new_ip

    @property
    def port(self):
        return self._TCP_PORT

    @port.setter
    def port(self, new_port):
        self._TCP_PORT = new_port

    @property
    def buffer_size(self):
        return self._BUFFER_SIZE

    @buffer_size.setter
    def buffer_size(self, new_buffer_size):
        self._BUFFER_SIZE = new_buffer_size

    @property
    def tasks_buffer_size(self):
        return self._TASKS_BUFFER_SIZE

    @tasks_buffer_size.setter
    def tasks_buffer_size(self, new_buffer_size):
        self._TASKS_BUFFER_SIZE = new_buffer_size

    @property
    def is_connected(self):
        return self._connected

    def connect(self):
        try:
            logger.debug('Opening TCP socket: {0}:{1}'.format(self.ip, self.port))
            self.s.connect((self.ip, self.port))
            self._connected = True
        except:
            logger.error('Cannot connect to socket {0}:{1}'.format(self.ip, self.port))
            self._connected = False
        return self.is_connected

    def send(self, message):
        if not self.is_connected:
            self.connect()
        logger.debug('Sending message: {0}'.format(message))
        self.s.send(message)
        response = self.s.recv(self._TASKS_BUFFER_SIZE)
        logger.debug('Received message: {0}'.format(response))
        return response

    def send_not_recv(self, message):
        if not self.is_connected:
            self.connect()
        logger.debug('Sending message: {0}'.format(message))
        self.s.send(message)

    def disconnect(self):
        logger.info('Closing socket: {0}'.format(self.s))
        self.s.close()
        self._connected = False

    def receive(self, size):
        resp = self.s.recv(size)
        return resp

    def listen(self):
        self.s.listen(1)

    def accept(self):
        conn, addr = self.s.accept()
        return conn

    def bind(self):
        self.s.bind((self._TCP_IP, self._TCP_PORT))
