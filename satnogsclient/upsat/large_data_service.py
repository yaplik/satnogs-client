import os
import traceback

from satnogsclient.upsat import packet_settings
from satnogsclient import settings as client_settings
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import packet


large_data_id = 0
socket = Udpsocket(('0.0.0.0', client_settings.LD_UPLINK_LISTEN_PORT))
gnuradio_sock = Udpsocket([])  # Gnuradio's udp listen port


def uplink(filename, info):
    filename = "/home/sleepwalker/Documents/large.txt"
    buf = bytearray(0)
    fo = open(filename, "rb")
    available_data_len = packet_settings.MAX_COMMS_PKT_SIZE - packet_settings.ECSS_HEADER_SIZE - packet_settings.ECSS_DATA_HEADER_SIZE - packet_settings.ECSS_CRC_SIZE - 3
    file_size = os.stat(filename)[6]  # get size of file
    remaining_bytes = file_size
    total_packets = file_size / available_data_len
    if file_size % available_data_len > 0:
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
        buf = bytearray(fo.read(data_size))
        packet_count_ms = packet_count & 0xFF00
        packet_count_ls = packet_count & 0x00FF
        buf.insert(0, large_data_id)
        buf.insert(0, packet_count_ls)
        buf.insert(0, packet_count_ms >> 8)

        if packet_count == 0:
            ser_subtype = packet_settings.TC_LD_FIRST_UPLINK
        elif packet_count == total_packets - 1:
            ser_subtype = packet_settings.TC_LD_LAST_UPLINK
        else:
            ser_subtype = packet_settings.TC_LD_INT_UPLINK
        ecss = {'type': 1,
             'app_id': 4,
             'size': data_size,
             'ack': 1,
             'ser_type': packet_settings.TC_LARGE_DATA_SERVICE,
             'ser_subtype': ser_subtype,
             'dest_id': 6,
             'data': buf,
             'seq_count': packet_count
             }
        hldlc_buf = packet.construct_packet(ecss, 'gnuradio')
        gnuradio_sock.sendto(hldlc_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))
        got_ack = 0
        retries = 0
        while (retries < 30) and (got_ack == 0):
            print ' retries = ', retries, 'got ack = ', got_ack
            try:
                print 'WAITING TO RECEIVE ACK!!!!'
                ack = socket.recv_timeout(client_settings.LD_UPLINK_TIMEOUT)
                ret = packet.deconstruct_packet(bytearray(ack[0]), [], 'gnuradio')
                ecss_dict = ret[0]
                print ecss_dict['data'][0], '    ', hex(packet_count)
                if hex(ord(ecss_dict['data'][2])) == hex(large_data_id):
                    print 'Seq count = ', (ecss_dict['data'][0] << 8) | ecss_dict['data'][1]
                    if ((ecss_dict['data'][0] << 8) | ecss_dict['data'][1]) == packet_count:
                        got_ack = 1
                        print 'Got the right ack!!!!'
                    else:
                        gnuradio_sock.sendto(hldlc_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))  # Resend previous frame
                        retries = retries + 1
                        print ' Got wrong sequence number ack'
                else:
                    print 'Wrond large data id'
                    retries = retries + 1
            except Exception, e:
                traceback.print_exc()
                print str(e)
                gnuradio_sock.sendto(hldlc_buf, (client_settings.GNURADIO_IP, client_settings.GNURADIO_UDP_PORT))
                retries = retries + 1
                print 'Timeout'
        if got_ack == 1:
            if ser_subtype == packet_settings.TC_LD_LAST_UPLINK:
                global large_data_id
                large_data_id = large_data_id + 1
            packet_count = packet_count + 1
        else:
            print 'Abort'
            return
