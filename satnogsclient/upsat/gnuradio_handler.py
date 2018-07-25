import logging
import subprocess
import os
import json

from satnogsclient import settings as client_settings

LOGGER = logging.getLogger('default')


def get_gnuradio_info():
    process = subprocess.Popen(
        ['python', '-m', 'satnogs.satnogs_info'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    gr_satnogs_info, _ = process.communicate()  # pylint: disable=W0612
    client_metadata = {
        'radio': {
            'name': 'gr-satnogs',
            'version': None,
            'rx_dexvice': client_settings.SATNOGS_RX_DEVICE,
            'ppm_error': client_settings.SATNOGS_PPM_ERROR,
            'if_gain': client_settings.SATNOGS_IF_GAIN,
            'rf_gain': client_settings.SATNOGS_RF_GAIN,
            'bb_gain': client_settings.SATNOGS_BB_GAIN,
            'antenna': client_settings.SATNOGS_ANTENNA,
        }
    }
    if process.returncode == 0:
        # Convert to valid JSON
        gr_satnogs_info = ''.join(gr_satnogs_info.partition('{')[1:])
        gr_satnogs_info = ''.join(gr_satnogs_info.partition('}')[:2])
        try:
            gr_satnogs_info = json.loads(gr_satnogs_info)
        except ValueError:
            client_metadata['radio']['version'] = 'invalid'
        else:
            if 'version' in gr_satnogs_info:
                client_metadata['radio']['version'] = gr_satnogs_info[
                    'version']
            else:
                client_metadata['radio']['version'] = 'unknown'
    return client_metadata


def exec_gnuradio(observation_file, waterfall_file, freq, baud, script_name,
                  decoded_data):
    arguments = {
        'filename': observation_file,
        'waterfall': waterfall_file,
        'rx_device': client_settings.SATNOGS_RX_DEVICE,
        'center_freq': str(freq),
        'script_name': script_name,
        'decoded_data': decoded_data
    }
    scriptname = arguments['script_name']
    arg_string = ' '
    if not scriptname:
        scriptname = client_settings.GNURADIO_SCRIPT_FILENAME
    rx_freq = arguments['center_freq']
    device = client_settings.SATNOGS_RX_DEVICE
    file_path = arguments['filename']
    waterfall_file_path = arguments['waterfall']
    arg_string += '--rx-sdr-device=' + device + ' '
    arg_string += '--rx-freq=' + rx_freq + ' '
    arg_string += '--file-path=' + file_path + ' '
    if arguments['waterfall'] != "":
        arg_string += '--waterfall-file-path=' + waterfall_file_path + ' '

    # If this is a CW observation pass the WPM parameter
    if scriptname == client_settings.GNURADIO_CW_SCRIPT_FILENAME and baud > 0:
        arg_string += '--wpm=' + str(int(baud)) + ' '
    # If this is a BPSK observation pass the baudrate parameter
    if scriptname == client_settings.GNURADIO_BPSK_SCRIPT_FILENAME and baud > 0:
        arg_string += '--baudrate=' + str(int(baud)) + ' '
    if client_settings.SATNOGS_RX_DEVICE and "--rx-sdr-device" not in arg_string:
        arg_string += '--rx-sdr-device=' + client_settings.SATNOGS_RX_DEVICE + ' '
    if (client_settings.SATNOGS_DOPPLER_CORR_PER_SEC
            and "--doppler-correction-per-sec" not in arg_string):
        arg_string += ('--doppler-correction-per-sec=' +
                       client_settings.SATNOGS_DOPPLER_CORR_PER_SEC + ' ')
    if client_settings.SATNOGS_LO_OFFSET and "--lo-offset" not in arg_string:
        arg_string += '--lo-offset=' + client_settings.SATNOGS_LO_OFFSET + ' '
    if client_settings.SATNOGS_PPM_ERROR and "--ppm" not in arg_string:
        arg_string += '--ppm=' + client_settings.SATNOGS_PPM_ERROR + ' '
    if client_settings.SATNOGS_IF_GAIN and "--if-gain" not in arg_string:
        arg_string += '--if-gain=' + client_settings.SATNOGS_IF_GAIN + ' '
    if client_settings.SATNOGS_RF_GAIN and "--rf-gain" not in arg_string:
        arg_string += '--rf-gain=' + client_settings.SATNOGS_RF_GAIN + ' '
    if client_settings.SATNOGS_BB_GAIN and "--bb-gain" not in arg_string:
        arg_string += '--bb-gain=' + client_settings.SATNOGS_BB_GAIN + ' '
    if client_settings.SATNOGS_ANTENNA and "--antenna" not in arg_string:
        arg_string += '--antenna=' + client_settings.SATNOGS_ANTENNA + ' '
    if client_settings.SATNOGS_DEV_ARGS and "--dev-args" not in arg_string:
        arg_string += '--dev-args=' + client_settings.SATNOGS_DEV_ARGS + ' '
    if client_settings.ENABLE_IQ_DUMP and "--enable-iq-dump" not in arg_string:
        arg_string += '--enable-iq-dump=' + str(
            int(client_settings.ENABLE_IQ_DUMP is True)) + ' '
    if client_settings.IQ_DUMP_FILENAME and "--iq-file-path" not in arg_string:
        arg_string += '--iq-file-path=' + client_settings.IQ_DUMP_FILENAME + ' '
    if not client_settings.DISABLE_DECODED_DATA and "--decoded-data-file-path" not in arg_string:
        arg_string += '--decoded-data-file-path=' + arguments['decoded_data'] + ' '

    LOGGER.info('Starting GNUradio python script')
    proc = subprocess.Popen(
        [scriptname + " " + arg_string], shell=True, preexec_fn=os.setsid)
    return proc
