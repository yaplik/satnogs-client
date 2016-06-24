import array
import time
import logging
import json
import cPickle

from satnogsclient.upsat import packet_settings
from satnogsclient import settings as client_settings
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import hldlc
from satnogsclient.upsat import packet


logger = logging.getLogger('satnogsclient')

udp_local_sock = Udpsocket(('127.0.0.1',client_settings.UDP_CLIENT_PORT)) # Port in which client listens for frames from gnuradio
ecss_feeder_sock = Udpsocket([]) # The socket with which we communicate with the ecss feeder thread
ld_socket = Udpsocket([])

def write(buf):
    udp_local_sock.sendto(buf, (client_settings.GNURADIO_IP,client_settings.GNURADIO_UDP_PORT))
    
def read_from_gnuradio():
    while True:
        conn = udp_local_sock.recv()
        buf_in = conn[0]
        ecss_dict = []
        ret = packet.deconstruct_packet(buf_in, ecss_dict, "gnuradio")
        ecss_dict = ret[0]
        pickled =  cPickle.dumps(ecss_dict)
        if ecss_dict['ser_type'] == packet_settings.TC_LARGE_DATA_SERVICE:
            ld_socket.sendto(pickled, ('127.0.0.1',client_settings.LD_UPLINK_LISTEN_PORT))
        else:
            ecss_feeder_sock.sendto(pickled,('127.0.0.1',client_settings.ECSS_LISTENER_UDP_PORT))
