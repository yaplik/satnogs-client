import serial
import array
import time
import logging
import cPickle

from flask import Flask, render_template, request, json, jsonify
from satnogsclient.upsat import packet_settings
from satnogsclient import settings as client_settings
from satnogsclient.upsat import hldlc
from satnogsclient.upsat import packet
from satnogsclient.observer.udpsocket import Udpsocket

logger = logging.getLogger('satnogsclient')
port = serial.Serial(client_settings.SERIAL_PORT, baudrate=9600, timeout=1.0)
ecss_feeder_sock = Udpsocket([]) # The socket with which we communicate with the ecss feeder thread
ld_socket = Udpsocket([])

def write(buf):
    print "Write in serial", buf
    port.write(buf)
    
def read_from_serial():
    buf_in = bytearray(0)
    while True:
        c = port.read()
        #print "From serial port read"
        if len(c) != 0:
            buf_in.append(c)
            if len(buf_in) == 1 and buf_in[0] != 0x7E:
                buf_in = bytearray(0)
            elif len(buf_in) > 1 and buf_in[len(buf_in) - 1] == 0x7E:
                print "From serial got pkt", ''.join('{:02x}'.format(x) for x in buf_in) 
                ecss_dict = []
                ret = packet.deconstruct_packet(buf_in, ecss_dict,"serial")
                ecss_dict = ret[0]
                pickled =  cPickle.dumps(ecss_dict)
                if ecss_dict['ser_type'] == packet_settings.TC_LARGE_DATA_SERVICE:
                    ld_socket.sendto(pickled, ('127.0.0.1',client_settings.LD_UPLINK_LISTEN_PORT))
                else:
                    ecss_feeder_sock.sendto(pickled,('127.0.0.1',client_settings.ECSS_LISTENER_UDP_PORT))
                buf_in = bytearray(0)

    