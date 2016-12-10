# -*- coding: utf-8 -*-
import logging
import socket


logger = logging.getLogger('satnogsclient')


class Udpsocket:
    """
    Class for handling udp sockets

    """

    _BUFFER_SIZE = 3000
    _connected = False
    """
    If the socket is used only for sending, an empty list for 'addr' is adequate
    If the socket will be used for receiving, a valid address tuple must be given
    """

    def __init__(self, addr):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if len(addr) == 2:
            self._UDP_IP = addr[0]
            self._UDP_PORT = addr[1]
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self._UDP_IP, self._UDP_PORT))

    @property
    def ip(self):
        return self._UDP_IP

    @ip.setter
    def ip(self, new_ip):
        self._UDP_IP = new_ip

    @property
    def port(self):
        return self._UDP_PORT

    @port.setter
    def port(self, new_port):
        self._UDP_PORT = new_port

    @property
    def buffer_size(self):
        return self._BUFFER_SIZE

    @buffer_size.setter
    def buffer_size(self, new_buffer_size):
        self._BUFFER_SIZE = new_buffer_size

    @property
    def is_connected(self):
        return self._connected

    def get_sock(self):
        return self.s

    def recv(self):
        if self.s.gettimeout() is not None:
            self.s.settimeout(None)
        data, addr = self.s.recvfrom(3000)
        return (data, addr)

    def sendto(self, message, addr):
        self.s.sendto(message, addr)

    def send_listen(self, message, addr):
        self.s.sendto(message, addr)
        ret = self.recv()
        return ret

    def recv_timeout(self, timeout):
        self.s.settimeout(timeout)
        conn = self.s.recvfrom(3000)
        return conn

    def set_timeout(self, sec):
        self.s.settimeout(sec)
