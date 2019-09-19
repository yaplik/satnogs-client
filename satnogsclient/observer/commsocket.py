from __future__ import absolute_import, division, print_function

import logging
import socket

LOGGER = logging.getLogger(__name__)


class Commsocket(object):
    """
    Handles connectivity with remote ctl demons
    Namely: rotctl and rigctl
    """

    _buffer_size = 2048
    _tasks_buffer_size = 10480
    _connected = False

    def __init__(self, ip_address, port):
        self._tcp_ip = ip_address
        self._tcp_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    @property
    def ip_address(self):
        return self._tcp_ip

    @ip_address.setter
    def ip_address(self, new_ip):
        self._tcp_ip = new_ip

    @property
    def port(self):
        return self._tcp_port

    @port.setter
    def port(self, new_port):
        self._tcp_port = new_port

    @property
    def buffer_size(self):
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, new_buffer_size):
        self._buffer_size = new_buffer_size

    @property
    def tasks_buffer_size(self):
        return self._tasks_buffer_size

    @tasks_buffer_size.setter
    def tasks_buffer_size(self, new_buffer_size):
        self._tasks_buffer_size = new_buffer_size

    @property
    def is_connected(self):
        return self._connected

    def connect(self):
        try:
            LOGGER.debug('Opening TCP socket: %s:%s', self.ip_address, self.port)
            self.sock.connect((self.ip_address, self.port))
            self._connected = True
        except socket.error:
            LOGGER.error('Cannot connect to socket %s:%s', self.ip_address, self.port)
            self._connected = False
        return self.is_connected

    def send(self, message):
        if not self.is_connected:
            self.connect()
        LOGGER.debug('Sending message: %s', message)
        try:
            self.sock.send(message.encode('ascii'))
        except socket.error:
            LOGGER.error('Cannot send to socket %s:%s', self.ip_address, self.port)

        response = self.sock.recv(self._tasks_buffer_size).decode('ascii')
        LOGGER.debug('Received message: %s', response)
        return response

    def send_not_recv(self, message):
        if not self.is_connected:
            self.connect()
        LOGGER.debug('Sending message: %s', message)
        self.sock.send(message.encode('ascii'))

    def disconnect(self):
        LOGGER.info('Closing socket: %s', self.sock)
        self.sock.close()
        self._connected = False

    def receive(self, size):
        resp = self.sock.recv(size)
        return resp

    def listen(self):
        self.sock.listen(1)

    def accept(self):
        conn, addr = self.sock.accept()  # pylint: disable=W0612
        return conn

    def bind(self):
        try:
            self.sock.bind((self._tcp_ip, self._tcp_port))
        except socket.error:
            LOGGER.error('Cannot bind socket %s:%s', self.ip_address, self.port)
            self.sock.close()
            self._connected = False
            self.bind()
