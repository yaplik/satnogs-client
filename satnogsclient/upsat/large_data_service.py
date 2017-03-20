import os
import traceback
import cPickle
import logging

from satnogsclient.upsat import packet_settings
from satnogsclient import settings as client_settings
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import packet
from time import sleep
from _socket import htons
from satnogsclient.upsat import ecss_logic_utils
import time
import binascii
from flask_socketio import SocketIO
socketio = SocketIO(message_queue='redis://')


logger = logging.getLogger('satnogsclient')

large_data_id = 0
total_downlink_packets = 0
uplink_socket = Udpsocket(('0.0.0.0', client_settings.LD_UPLINK_LISTEN_PORT))
downlink_socket = Udpsocket(('0.0.0.0', client_settings.LD_DOWNLINK_LISTEN_PORT))
gnuradio_sock = Udpsocket([])  # Gnuradio's udp listen port


def uplink(buf_in):
    buf = bytearray(0)
    available_data_len = packet_settings.MAX_COMMS_PKT_SIZE - packet_settings.ECSS_HEADER_SIZE - packet_settings.ECSS_DATA_HEADER_SIZE - packet_settings.ECSS_CRC_SIZE - 3
    buffer_size = len(buf_in)
    remaining_bytes = buffer_size
    total_packets = buffer_size / available_data_len
    if buffer_size % available_data_len > 0:
        total_packets = total_packets + 1
    packet_count = 0
    data_size = 0
    while remaining_bytes > 0:
        if remaining_bytes >= available_data_len:
            data_size = available_data_len
            remaining_bytes = remaining_bytes - available_data_len
        else:
            data_size = remaining_bytes
            remaining_bytes = 0
        buf = buf_in[0:data_size]
        del buf_in[0:data_size]
        packet_count_htons = htons(packet_count)
        packet_count_ms = (packet_count_htons & 0xFF00) >> 8
        packet_count_ls = packet_count_htons & 0x00FF
        buf.insert(0, packet_count_ls)
        buf.insert(0, packet_count_ms)
        buf.insert(0, large_data_id)

        if packet_count == 0:
            ser_subtype = packet_settings.TC_LD_FIRST_UPLINK
        elif packet_count == total_packets - 1:
            ser_subtype = packet_settings.TC_LD_LAST_UPLINK
        else:
            ser_subtype = packet_settings.TC_LD_INT_UPLINK
        ecss = {'type': 1,
                'app_id': 4,
                'size': len(buf),
                'ack': 1,
                'ser_type': packet_settings.TC_LARGE_DATA_SERVICE,
                'ser_subtype': ser_subtype,
                'dest_id': 6,
                'data': buf,
                'seq_count': packet_count}
        hldlc_buf = packet.construct_packet(ecss, os.environ['BACKEND'])
        gnuradio_sock.sendto(hldlc_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))
        got_ack = 0
        retries = 0
        while (retries < 30) and (got_ack == 0):
            logger.info('[LD] ECSS to be sent: %s', str(ecss))
            logger.info('[LD] Retries = %s, got ACK = %s', retries, got_ack)
            try:
                logger.info('Waiting for ack')
                ack = uplink_socket.recv_timeout(client_settings.LD_UPLINK_TIMEOUT)
                ecss_dict = cPickle.loads(ack[0])
                if len(ecss_dict) == 0:
                    continue
                if hex(ecss_dict['data'][0]) == hex(large_data_id):
                    logger.info('[LD] Seq count = %s', str(((ecss_dict['data'][0] << 8) | ecss_dict['data'][1])))
                    if ((ecss_dict['data'][2] << 8) | ecss_dict['data'][1]) == packet_count:
                        got_ack = 1
                        sleep(0.5)
                        logger.info('[LD] Got the right ack')
                    else:
                        sleep(0.5)
                        gnuradio_sock.sendto(hldlc_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))  # Resend previous frame
                        retries = retries + 1
                        logger.error('[LD] Wrong large data sequence number')
                else:
                    logger.error('[LD] Wrong large data ID')
                    retries = retries + 1
            except Exception, e:
                traceback.print_exc()
                logger.error('[LD] exception: %s', str(e))
                sleep(0.5)
                gnuradio_sock.sendto(hldlc_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))
                retries = retries + 1
                logger.error('[LD] [LD] Timed out')
        if got_ack == 1:
            if ser_subtype == packet_settings.TC_LD_LAST_UPLINK:
                global large_data_id
                large_data_id = large_data_id + 1
            packet_count = packet_count + 1
        else:
            logger.info('[LD] Aborted operation')
            return


def downlink():
    prev_id = -1
    end_time = 0
    receiving = False
    received_packets = {}
    while 1:
        if receiving:
            try:
                logger.info('[LD] Downlink thread awaits for next frame')
                data = downlink_socket.recv_timeout(end_time - time.time())
                logger.info('[LD] Downlink packet received!')
            except:
                logger.info('[LD] Downlink operation not completed on time. Going to fallback operation')
                ret = fallback(received_packets, prev_id)
                prev_id = -1
                receiving = False
                if ret[1] == 1:
                    frame = construct_downlink_packet(received_packets)
                    logger.debug('[LD] Packet received is: %s', str(binascii.hexlify(frame)))
                    logger.info('[LD] Downlink operation completed')
                    decode_and_send(frame)
                    logger.info('[LD] Packet sent to front end')
                    received_packets.clear()
                    global total_downlink_packets
                    total_downlink_packets = 0
                    continue
                else:
                    received_packets.clear()
                    global total_downlink_packets
                    total_downlink_packets = 0
                    continue
            ecss_dict = cPickle.loads(data[0])
        else:
            logger.info('[LD] Downlink thread waiting for first downlink packet')
            data = downlink_socket.recv()
            logger.info('[LD] First downlink packet received')
            end_time = time.time() + client_settings.LD_DOWNLINK_TIMEOUT
            ecss_dict = cPickle.loads(data[0])
            receiving = True
            prev_id = ecss_dict['data'][0]
        if len(ecss_dict) == 0:
            logger.error('[LD] Received empty ecss_dict. Ignoring frame')
            continue
        seq_count = (ecss_dict['data'][2] << 8) | ecss_dict['data'][1]
        if hex(prev_id) != hex(ecss_dict['data'][0]):
            logger.error('[LD] Wrong large data id during downlink operation. Aborting')
            prev_id = -1
            receiving = False
            received_packets.clear()
        buf = ecss_dict['data'][3:ecss_dict['size']]
        received_packets[seq_count] = buf
        # global total_downlink_packets
        # total_downlink_packets += 1
        if ecss_dict['ser_subtype'] == packet_settings.TM_LD_LAST_DOWNLINK:
            global total_downlink_packets
            total_downlink_packets = seq_count + 1
            ret = fallback(received_packets, prev_id)
            logger.debug('[LD] Returned from callback')
            prev_id = -1
            receiving = False
            if ret[1] == 1:
                frame = construct_downlink_packet(received_packets)
                logger.debug('[LD] Packet received is: %s', str(binascii.hexlify(frame)))
                logger.info('[LD] Downlink operation completed')
                decode_and_send(frame)
                logger.info('[LD] Packet sent to front end')
                received_packets.clear()
                global total_downlink_packets
                total_downlink_packets = 0
            else:
                received_packets.clear()
                global total_downlink_packets
                total_downlink_packets = 0
                continue


def fallback(received_packets, prev_id):
    logger.info('[LD] Callback function takes over')
    logger.info('[LD] Total packets received: ' + str(total_downlink_packets))
    finished = False
    requested_seq_num = 0
    packet_retries = 0
    while not finished:
        logger.info('[LD] Requested sequence number =  ' + str(requested_seq_num))
        if requested_seq_num not in received_packets:
            request_packet(prev_id, requested_seq_num, 'gnuradio')
            try:
                end_time = time.time() + client_settings.LD_DOWNLINK_SMALL_TIMEOUT  # Maybe another timeout should be considered here
                data = downlink_socket.recv_timeout(end_time - time.time())
            except IOError:
                if packet_retries < client_settings.LD_DOWNLINK_RETRIES_LIM:
                    logger.error('[LD] Fallback operation for packet number ' + str(requested_seq_num) + ' was not completed on time.Retrying')
                    packet_retries += 1
                    continue
                else:
                    logger.error('[LD] Fallback operation for packet number ' + str(requested_seq_num) + ' was not completed.Aborting')
                    return(received_packets, -1)
            ecss_dict = cPickle.loads(data[0])
            if len(ecss_dict) == 0:
                logger.error('[LD] Received empty ecss dict in fallback operation. Ignoring frame')
                continue
            seq_count = (ecss_dict['data'][2] << 8) | ecss_dict['data'][1]
            if seq_count != requested_seq_num:
                if packet_retries < client_settings.LD_DOWNLINK_RETRIES_LIM:
                    logger.error('[LD] Fallback operation for packet number ' + str(requested_seq_num) + ' was not completed.Wrong seq num.Retrying')
                    packet_retries += 1
                    continue
                else:
                    logger.error('[LD] Fallback operation for packet number ' + str(requested_seq_num) + ' was not completed.Wrong seq num.Aborting')
                    return(received_packets, -1)
            if hex(prev_id) != hex(ecss_dict['data'][0]):
                logger.error('[LD] Wrong large data id during fallback of downlink operation. Aborting')
                if packet_retries < client_settings.LD_DOWNLINK_RETRIES_LIM:
                    logger.error('[LD] Fallback operation for packet number ' + str(requested_seq_num) + ' was not completed.Wrong LD ID.Retrying')
                    packet_retries += 1
                    continue
                else:
                    logger.error('[LD] Fallback operation for packet number ' + str(requested_seq_num) + ' was not completed.Wrong LD ID.Aborting')
                    return(received_packets, -1)
            buf = ecss_dict['data'][3:ecss_dict['size']]
            received_packets[seq_count] = buf
            requested_seq_num += 1
            packet_retries = 0
            if ecss_dict['ser_subtype'] == packet_settings.TM_LD_LAST_DOWNLINK:
                global total_downlink_packets
                total_downlink_packets = seq_count + 1
                finished = True
                return(received_packets, 1)
        else:
            requested_seq_num += 1
        if total_downlink_packets > 0 and requested_seq_num == total_downlink_packets:  # The count has reached the final sequence number meaning that all packets were received
            finished = True
            return(received_packets, 1)


def construct_downlink_packet(received_packets):
    frame = bytearray()
    frame.extend(received_packets[0])
    for i in range(1, total_downlink_packets):
        frame.extend(received_packets[i])
    return frame


def request_packet(ld_id, ld_num, backend):
    buf = bytearray(0)
    packet_count_htons = htons(ld_num)
    packet_count_ms = (packet_count_htons & 0xFF00) >> 8
    packet_count_ls = packet_count_htons & 0x00FF
    buf.insert(0, packet_count_ls)
    buf.insert(0, packet_count_ms)
    buf.insert(0, ld_id)
    ecss = {
        'type': 1,
        'app_id': 4,
        'size': len(buf),
        'ack': 1,  # Ack 1?????
        'ser_type': packet_settings.TC_LARGE_DATA_SERVICE,
        'ser_subtype': packet_settings.TC_LD_REPEAT_DOWNLINK,
        'dest_id': 6,
        'data': buf,
        'seq_count': 0
    }
    ready_buf = packet.construct_packet(ecss, backend)
    gnuradio_sock.sendto(ready_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))


def decode_and_send(buf_in):
    ecss_dict = {}
    ret = packet.deconstruct_packet(buf_in, ecss_dict, "gnuradio")
    ecss_dict = ret[0]
    data = ecss_logic_utils.ecss_logic(ecss_dict)
    socketio.emit('backend_msg', data, namespace='/control_rx', callback=success_message_to_frontend())


def success_message_to_frontend():
    logger.debug('[LD] Successfuly emit to frontend')
