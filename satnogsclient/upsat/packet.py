import logging
import socket
import binascii
import struct
import ctypes

from satnogsclient.upsat import packet_settings
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import hldlc

logger = logging.getLogger('satnogsclient')



def ecss_encoder(port):
    logger.info('Started ecss encoder')
    sock = Commsocket('127.0.0.1',port)
    sock.bind()
    sock.listen()
    while 1:
        conn = sock.accept()
        if conn:
            data = conn.recv(sock.tasks_buffer_size)
            ecss_packetizer(data)

def ecss_depacketizer(buf,dict_out):
    size = len(buf)
    print binascii.hexlify(buf)
    assert((buf != 0) == True)
    assert((size > packet_settings.MIN_PKT_SIZE and size < packet_settings.MAX_PKT_SIZE) == True)
    print "I should see that"
    tmp_crc1 = buf[size - 1];
    tmp_crc2 = 0
    for i in range(0,size -2):
        tmp_crc2 = tmp_crc2 ^ buf[i]

    ver = buf[0] >> 5;

    pkt_type = (buf[0] >> 4) & 0x01;
    dfield_hdr = (buf[0] >> 3) & 0x01;

    pkt_app_id = buf[1];

    pkt_seq_flags = buf[2] >> 6;
    t = bytearray(2)
    t[0] = buf[2]
    t[1] = buf[3]
    t.reverse()
    #pkt_seq_count = t & 0x3FFF;
    pkt_seq_count = (((t[0] & 0x3FF) << 8) | (t[1] & 0xFF))

    pkt_len = (buf[4] << 8) | buf[5]

    ccsds_sec_hdr = buf[6] >> 7;

    tc_pus = buf[6] >> 4;

    pkt_ack = 0x07 & buf[6];

    pkt_ser_type = buf[7];
    pkt_ser_subtype = buf[8];
    pkt_dest_id = buf[9];

    pkt_verification_state = packet_settings.SATR_PKT_INIT

    if not ((pkt_app_id < packet_settings.LAST_APP_ID) == True) :
        pkt_verification_state = packet_settings.SATR_PKT_ILLEGAL_APPID
        return (dict_out, packet_settings.SATR_PKT_ILLEGAL_APPID)


    if not ((pkt_len == size - packet_settings.ECSS_HEADER_SIZE - 1) == True):
        print "INV LEN", pkt_len, " ", size - packet_settings.ECSS_HEADER_SIZE - 1
        return (dict_out, packet_settings.SATR_PKT_INV_LEN)

    pkt_len = pkt_len - packet_settings.ECSS_DATA_HEADER_SIZE - packet_settings.ECSS_CRC_SIZE + 1;

    if not ((tmp_crc1 == tmp_crc2) == True) :
        pkt_verification_state = packet_settings.SATR_PKT_INC_CRC
        return (dict_out, packet_settings.SATR_PKT_INC_CRC)

    if not((packet_settings.SERVICES_VERIFICATION_TC_TM[pkt_ser_type][pkt_ser_subtype][pkt_type] == 1) == True) :
        pkt_verification_state = packet_settings.SATR_PKT_ILLEGAL_PKT_TP
        return (dict_out, packet_settings.SATR_PKT_ILLEGAL_PKT_TP)

    if not ((ver == packet_settings.ECSS_VER_NUMBER) == True) :
        pkt_verification_state = packet_settings.SATR_ERROR
        return (dict_out, packet_settings.SATR_ERROR)

    if not ((tc_pus == packet_settings.ECSS_PUS_VER) == True) :
        return (dict_out, packet_settings.SATR_ERROR)

    if not ((ccsds_sec_hdr == packet_settings.ECSS_SEC_HDR_FIELD_FLG) == True) :
        print "INV HDR FIELD", ccsds_sec_hdr
        return (dict_out, packet_settings.SATR_ERROR)

    if not ((pkt_type == packet_settings.TC or pkt_type == packet_settings.TM) == True) :
        print "INV TYPE", pkt_type
        return (dict_out, packet_settings.SATR_ERROR)

    if not ((dfield_hdr == packet_settings.ECSS_DATA_FIELD_HDR_FLG) == True) :
        pkt_verification_state = packet_settings.SATR_ERROR
        return (dict_out, packet_settings.SATR_ERROR)

    if not ((pkt_ack == packet_settings.TC_ACK_NO or pkt_ack == packet_settings.TC_ACK_ACC) == True) :
        pkt_verification_state = packet_settings.SATR_ERROR
        return (dict_out, packet_settings.SATR_ERROR)

    if not ((pkt_seq_flags == packet_settings.TC_TM_SEQ_SPACKET) == True) :
        pkt_verification_state = packet_settings.SATR_ERROR
        return (dict_out, packet_settings.SATR_ERROR)
    pkt_data = bytes(pkt_len)

    pkt_data = buf[packet_settings.ECSS_DATA_OFFSET : size -2]
    dict_out={'type':pkt_type,
             'app_id':pkt_app_id,
             'size':pkt_len,
             'ack':pkt_ack,
             'ser_type':pkt_ser_type,
             'ser_subtype':pkt_ser_subtype,
             'dest_id':pkt_dest_id,
             'data':pkt_data
             }
    print "I should see that also" , dict_out
    return (dict_out, packet_settings.SATR_OK)

def ecss_decoder(port):
    logger.info('Started ecss decoder')
    sock = Commsocket('127.0.0.1',port)
    sock.bind()
    sock.listen()
    while 1:
        conn = sock.accept()
        if conn:
            data = conn.recv(sock.tasks_buffer_size)
            ecss_depacketizer(data)



def ecss_packetizer(ecss,buf):
    sock = Commsocket(packet_settings.FRAME_RECEIVER_IP, packet_settings.FRAME_RECEIVER_PORT)
    assert(((ecss['type'] == 0) or (ecss['type'] == 1)) == True )
    assert((ecss['app_id'] < packet_settings.LAST_APP_ID) == True)
    data_size = ecss['size']
    app_id = ecss['app_id']
    app_id_ms = app_id & 0xFF00
    app_id_ls = app_id & 0x00FF
    app_id_ms = app_id_ms >> 8
    buf[0] = ( packet_settings.ECSS_VER_NUMBER << 5 | ecss['type']
               << 4 | packet_settings.ECSS_DATA_FIELD_HDR_FLG << 3 | app_id_ms);
    buf[1] = app_id_ls
    seq_flags = packet_settings.TC_TM_SEQ_SPACKET
    seq_count = ecss['seq_count']
    seq_count_ms = seq_count & 0xFF00
    seq_count_ls = seq_count & 0x00FF
    seq_count_ms = seq_count >> 8
    buf[2] = (seq_flags << 6 | seq_count_ms)
    buf[3] = seq_count_ls
    if ecss['type'] == 0 :
        buf[6] = packet_settings.ECSS_PUS_VER << 4 ;
    elif ecss['type'] == 1 :
        buf[6] = ( packet_settings.ECSS_SEC_HDR_FIELD_FLG << 7 | packet_settings.ECSS_PUS_VER << 4 | ecss['ack']);
    buf[7] = ecss['ser_type']
    buf[8] = ecss['ser_subtype']
    buf[9] = ecss['dest_id']
    buf_pointer = packet_settings.ECSS_DATA_OFFSET
    for i in range(0,data_size):
        buf[buf_pointer + i] = ecss['data'][i]
    data_w_headers = data_size + packet_settings.ECSS_DATA_HEADER_SIZE + packet_settings.ECSS_CRC_SIZE -1
    packet_size_ms = data_w_headers  & 0xFF00
    packet_size_ls = data_w_headers  & 0x00FF
    buf[4] = packet_size_ms >> 8
    buf[5] = packet_size_ls
    buf_pointer = buf_pointer + data_size
    for i in range(0,buf_pointer):
        buf[buf_pointer + 1] = buf[buf_pointer + 1] ^ buf[i]

    size = buf_pointer + 2
    assert((size > packet_settings.MIN_PKT_SIZE and size < packet_settings.MAX_PKT_SIZE) == True)
    return packet_settings.SATR_OK

def comms_off():
    sock = Udpsocket([])
    data = ctypes.create_string_buffer(25)
    data[0:9] = 'RF SW CMD'
    struct.pack_into("<I",data,9,0x593d55df)
    struct.pack_into("<I",data,13,0x4d2f84c0)
    struct.pack_into("<I",data,17,0x24d60191)
    struct.pack_into("<I",data,21,0x9287b5fd)
    d = bytearray(data)
    sock.sendto(d,(packet_settings.FRAME_RECEIVER_IP, packet_settings.FRAME_RECEIVER_PORT))

def comms_on():
    sock = Udpsocket([])
    data = ctypes.create_string_buffer(25)
    data[0:9] = 'RF SW CMD'
    struct.pack_into("<I",data,9,0xda4942a9)
    struct.pack_into("<I",data,13,0xa7a45d61)
    struct.pack_into("<I",data,17,0x413981b)
    struct.pack_into("<I",data,21,0xa94ee2d3)
    d = bytearray(data)
    sock.sendto(d,(packet_settings.FRAME_RECEIVER_IP, packet_settings.FRAME_RECEIVER_PORT))

def construct_packet(ecss_dict,backend):
    print 'ecss to be sent ',ecss_dict
    if backend == "serial":
        out_buf = bytearray(0)
        packet_size = len(ecss_dict['data']) + packet_settings.ECSS_DATA_HEADER_SIZE + packet_settings.ECSS_CRC_SIZE + packet_settings.ECSS_HEADER_SIZE
        ecssbuf = bytearray(packet_size)
        ecss_packetizer(ecss_dict, ecssbuf)
        hldlc.HLDLC_frame(ecssbuf,out_buf)
    elif backend == "gnuradio":
        packet_size = len(ecss_dict['data']) + packet_settings.ECSS_DATA_HEADER_SIZE + packet_settings.ECSS_CRC_SIZE + packet_settings.ECSS_HEADER_SIZE
        out_buf = bytearray(packet_size)
        ecss_packetizer(ecss_dict, out_buf)
    return out_buf

def deconstruct_packet(buf_in, ecss_dict , backend):
    if backend == 'serial':
        hldlc_buf = bytearray(0)
        hldlc.HLDLC_deframe(buf_in, hldlc_buf)
        print "HLDLC ", ''.join('{:02x}'.format(x) for x in buf_in)  ," ", ''.join('{:02x}'.format(x) for x in hldlc_buf)
        res = ecss_depacketizer(hldlc_buf,ecss_dict)
        print "the result is ", res
    elif backend == 'gnuradio':
        res = ecss_depacketizer(buf_in,ecss_dict)
    return res






