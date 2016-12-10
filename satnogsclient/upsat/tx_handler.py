from satnogsclient.upsat import serial_handler
from satnogsclient.upsat import gnuradio_handler
import os
import logging

logger = logging.getLogger('satnogsclient')


def send_to_backend(buf):
    logger.debug('Send to backend called with backend %s', os.environ['BACKEND'])
    curr_backend = os.environ['BACKEND']
    if curr_backend != 'gnuradio' and curr_backend != 'serial':
        return 0
    if curr_backend == 'gnuradio':
        gnuradio_handler.write_to_gnuradio(buf)
        return 1
    if curr_backend == 'serial':
        serial_handler.write_to_serial(buf)
        return 1
