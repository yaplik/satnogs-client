import serial
import logging
import cPickle

from satnogsclient.upsat import packet_settings
from satnogsclient import settings as client_settings
from satnogsclient.upsat import packet
from satnogsclient.observer.udpsocket import Udpsocket

logger = logging.getLogger('satnogsclient')
port = 0
ecss_feeder_sock = ''
ui_listener_sock = ''
ld_socket = ''


def init():
    global port
    global ecss_feeder_sock
    global ui_listener_sock
    global ld_socket
    try:
        port = serial.Serial(client_settings.SATNOGS_SERIAL_PORT, baudrate=9600, timeout=1.0)
    except serial.SerialException as e:
        logger.error('Could not open serial port. Error occured')
        logger.error(e)
        return
    ecss_feeder_sock = Udpsocket([])  # The socket with which we communicate with the ecss feeder thread
    ui_listener_sock = Udpsocket(('127.0.0.1', client_settings.BACKEND_FEEDER_PORT))
    ld_socket = Udpsocket([])


def close():
    global port
    try:
        if port != 0:
            port.close()
    except serial.SerialException as e:
        logger.error('Could not close serial port. Error occured')
        logger.error(e)
        return


def write_to_serial(buf):
    logger.info('Sending data to serial: %s', ''.join('{:02x}'.format(x) for x in buf))
    global port
    try:
        if port != 0:
            port.write(buf)
        else:
            logger.info('Serial port is closed')
    except serial.SerialException as e:
        logger.error('Could not write to serial port. Error occured')
        logger.error(e)


def read_from_serial():
    global port
    global ecss_feeder_sock
    global ui_listener_sock
    global ld_socket
    logger.info('Started serial listener process')
    buf_in = bytearray(0)
    while True:
        try:
            if port != 0:
                c = port.read()
            else:
                logger.info('Serial port is closed')
        except serial.SerialException as e:
            logger.error('Could not read from serial port. Error occured')
            logger.error(e)
            return
        if len(c) != 0:
            buf_in.append(c)
            if len(buf_in) == 1 and buf_in[0] != 0x7E:
                buf_in = bytearray(0)
            elif len(buf_in) > 1 and buf_in[len(buf_in) - 1] == 0x7E:
                logger_packet = ''.join('{:02x}'.format(x) for x in buf_in)
                logger.info('Received packet from serial.')
                logger.debug('From serial: %s', logger_packet)
                ecss_dict = {}
                ret = packet.deconstruct_packet(buf_in, ecss_dict, "serial")
                ecss_dict = ret[0]
                pickled = cPickle.dumps(ecss_dict)
                logger.debug('Sending to UDP: %s', ecss_dict)
                if len(ecss_dict) == 0:
                    logger.error('Ecss Dictionary not properly constructed. Error occured')
                    continue
                try:
                    if not ecss_dict and ecss_dict['ser_type'] == packet_settings.TC_LARGE_DATA_SERVICE:
                        ld_socket.sendto(pickled, ('127.0.0.1', client_settings.LD_UPLINK_LISTEN_PORT))
                    else:
                        ecss_feeder_sock.sendto(pickled, ('127.0.0.1', client_settings.ECSS_FEEDER_UDP_PORT))
                except KeyError:
                    logger.error('Ecss Dictionary not properly constructed. Error occured. Key \'ser_type\' not in dictionary')
                buf_in = bytearray(0)
