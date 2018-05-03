from __future__ import absolute_import, division, print_function

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
    arg_string = ' '
    if not script_name:
        script_name = client_settings.GNURADIO_SCRIPT_FILENAME
    device = client_settings.SATNOGS_RX_DEVICE
    arg_string += '--rx-sdr-device=' + device + ' '
    arg_string += '--rx-freq=' + str(freq) + ' '
    arg_string += '--file-path=' + observation_file + ' '
    if waterfall_file != "":
        arg_string += '--waterfall-file-path=' + waterfall_file + ' '

    # If this is a CW observation pass the WPM parameter
    if script_name == client_settings.GNURADIO_CW_SCRIPT_FILENAME and baud > 0:
        arg_string += '--wpm=' + str(int(baud)) + ' '
    # If this is a BPSK observation pass the baudrate parameter
    if script_name == client_settings.GNURADIO_BPSK_SCRIPT_FILENAME and baud > 0:
        arg_string += '--baudrate=' + str(int(baud)) + ' '
    if client_settings.SATNOGS_DOPPLER_CORR_PER_SEC:
        arg_string += ('--doppler-correction-per-sec=' +
                       client_settings.SATNOGS_DOPPLER_CORR_PER_SEC + ' ')
    if client_settings.SATNOGS_LO_OFFSET:
        arg_string += '--lo-offset=' + client_settings.SATNOGS_LO_OFFSET + ' '
    if client_settings.SATNOGS_RIG_PORT:
        arg_string += '--rigctl-port=' + str(
            client_settings.SATNOGS_RIG_PORT) + ' '
    if client_settings.SATNOGS_PPM_ERROR:
        arg_string += '--ppm=' + client_settings.SATNOGS_PPM_ERROR + ' '
    if client_settings.SATNOGS_IF_GAIN:
        arg_string += '--if-gain=' + client_settings.SATNOGS_IF_GAIN + ' '
    if client_settings.SATNOGS_RF_GAIN:
        arg_string += '--rf-gain=' + client_settings.SATNOGS_RF_GAIN + ' '
    if client_settings.SATNOGS_BB_GAIN:
        arg_string += '--bb-gain=' + client_settings.SATNOGS_BB_GAIN + ' '
    if client_settings.SATNOGS_ANTENNA:
        arg_string += '--antenna=' + client_settings.SATNOGS_ANTENNA + ' '
    if client_settings.SATNOGS_DEV_ARGS:
        arg_string += '--dev-args=' + client_settings.SATNOGS_DEV_ARGS + ' '
    if client_settings.ENABLE_IQ_DUMP:
        arg_string += '--enable-iq-dump=' + str(
            int(client_settings.ENABLE_IQ_DUMP is True)) + ' '
    if client_settings.IQ_DUMP_FILENAME:
        arg_string += '--iq-file-path=' + client_settings.IQ_DUMP_FILENAME + ' '
    if not client_settings.DISABLE_DECODED_DATA:
        arg_string += '--decoded-data-file-path=' + decoded_data + ' '

    LOGGER.info('Starting GNUradio python script')
    proc = subprocess.Popen(
        [script_name + " " + arg_string], shell=True, preexec_fn=os.setsid)
    return proc
