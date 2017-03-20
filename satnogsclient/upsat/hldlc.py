import logging

from satnogsclient.upsat import packet_settings

logger = logging.getLogger('satnogsclient')
log_path = ""


def HLDLC_deframe(buf_in, buf_out):
    size = len(buf_in)
    logger.debug('HLDLC size: %s', size)

    r = range(1, size)
    for i in r:
        if buf_in[i] == packet_settings.HLDLC_START_FLAG:
            return packet_settings.SATR_EOT
        elif buf_in[i] == packet_settings.HLDLC_CONTROL_FLAG:
            r.remove(i + 1)  # it skips the next ieteration
            i = i + 1
            if not (i < size - 1):
                return packet_settings.SATR_ERROR
            if buf_in[i] == 0x5E:
                buf_out.append(0x7E)
            elif buf_in[i] == 0x5D:
                buf_out.append(0x7D)
            else:
                return packet_settings.SATR_ERROR
        else:
            buf_out.append(buf_in[i])

    return packet_settings.SATR_ERROR


def HLDLC_frame(buf_in, buf_out):

    assert((buf_in != 0) and (buf_out != 0))
    assert(len(buf_in) <= packet_settings.MAX_PKT_SIZE)

    size = len(buf_in)

    for i in range(0, size):
        if i == 0:
            buf_out.append(packet_settings.HLDLC_START_FLAG)
            buf_out.append(buf_in[0])
        elif i == size - 1:
            if buf_in[i] == packet_settings.HLDLC_START_FLAG:
                buf_out.append(packet_settings.HLDLC_CONTROL_FLAG)
                buf_out.append(0x5E)
            elif buf_in[i] == packet_settings.HLDLC_CONTROL_FLAG:
                buf_out.append(packet_settings.HLDLC_CONTROL_FLAG)
                buf_out.append(0x5D)
            else:
                buf_out.append(buf_in[i])
            buf_out.append(packet_settings.HLDLC_START_FLAG)
            return packet_settings.SATR_EOT
        elif buf_in[i] == packet_settings.HLDLC_START_FLAG:
            buf_out.append(packet_settings.HLDLC_CONTROL_FLAG)
            buf_out.append(0x5E)
        elif buf_in[i] == packet_settings.HLDLC_CONTROL_FLAG:
            buf_out.append(packet_settings.HLDLC_CONTROL_FLAG)
            buf_out.append(0x5D)
        else:
            buf_out.append(buf_in[i])
    return packet_settings.SATR_ERROR
