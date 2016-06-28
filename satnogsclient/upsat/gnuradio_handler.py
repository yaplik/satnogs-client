import logging
import cPickle

from satnogsclient.upsat import packet_settings
from satnogsclient import settings as client_settings
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import packet


logger = logging.getLogger('satnogsclient')

backend_listener_sock = Udpsocket(('127.0.0.1', client_settings.BACKEND_LISTENER_PORT))  # Port in which client listens for frames from gnuradio
ui_listener_sock = Udpsocket(('127.0.0.1', client_settings.BACKEND_FEEDER_PORT))
ecss_feeder_sock = Udpsocket([])  # The socket with which we communicate with the ecss feeder thread
backend_feeder_sock = Udpsocket([])
ld_socket = Udpsocket([])


def write_to_gnuradio(buf):
    backend_feeder_sock.sendto(buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))


def read_from_gnuradio():
    print 'Started gnuradio listener process'
    while True:
        conn = backend_listener_sock.recv()
        buf_in = conn[0]
        ecss_dict = []
        ret = packet.deconstruct_packet(buf_in, ecss_dict, "gnuradio")
        ecss_dict = ret[0]
        pickled = cPickle.dumps(ecss_dict)
        if ecss_dict['ser_type'] == packet_settings.TC_LARGE_DATA_SERVICE:
            ld_socket.sendto(pickled, ('127.0.0.1', client_settings.LD_UPLINK_LISTEN_PORT))
        else:
            ecss_feeder_sock.sendto(pickled, ('127.0.0.1', client_settings.ECSS_LISTENER_UDP_PORT))
