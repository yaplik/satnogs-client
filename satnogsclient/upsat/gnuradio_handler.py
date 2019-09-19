from __future__ import absolute_import, division, print_function

import json
import logging
import os
import subprocess

from satnogsclient import settings as client_settings

LOGGER = logging.getLogger(__name__)


def get_gnuradio_info():
    process = subprocess.Popen(['python', '-m', 'satnogs.satnogs_info'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    gr_satnogs_info, _ = process.communicate()  # pylint: disable=W0612
    client_metadata = {
        'radio': {
            'name': 'gr-satnogs',
            'version': None,
            'rx_device': client_settings.SATNOGS_RX_DEVICE,
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
                client_metadata['radio']['version'] = gr_satnogs_info['version']
            else:
                client_metadata['radio']['version'] = 'unknown'
    return client_metadata


def exec_gnuradio(observation_file, waterfall_file, freq, baud, script_name, decoded_data):
    if not script_name:
        script_name = client_settings.GNURADIO_SCRIPT_FILENAME
    device = client_settings.SATNOGS_RX_DEVICE
    args = [
        script_name, '--rx-sdr-device=' + device, '--rx-freq=' + str(freq),
        '--file-path=' + observation_file
    ]
    if waterfall_file != "":
        args += ['--waterfall-file-path=' + waterfall_file]

    # If this is a CW observation pass the WPM parameter
    if script_name == client_settings.GNURADIO_CW_SCRIPT_FILENAME and baud > 0:
        args += ['--wpm=' + str(int(baud))]
    # If this is a BPSK/FSK/MSK observation pass the baudrate parameter
    if script_name in [
            client_settings.GNURADIO_BPSK_SCRIPT_FILENAME,
            client_settings.GNURADIO_GFSK_RKTR_SCRIPT_FILENAME,
            client_settings.GNURADIO_FSK_SCRIPT_FILENAME,
            client_settings.GNURADIO_MSK_SCRIPT_FILENAME
    ] and baud > 0:
        args += ['--baudrate=' + str(int(baud))]
    if client_settings.SATNOGS_DOPPLER_CORR_PER_SEC:
        args += ['--doppler-correction-per-sec=' + client_settings.SATNOGS_DOPPLER_CORR_PER_SEC]
    if client_settings.SATNOGS_LO_OFFSET:
        args += ['--lo-offset=' + client_settings.SATNOGS_LO_OFFSET]
    if client_settings.SATNOGS_RIG_PORT:
        args += ['--rigctl-port=' + str(client_settings.SATNOGS_RIG_PORT)]
    if client_settings.SATNOGS_PPM_ERROR:
        args += ['--ppm=' + client_settings.SATNOGS_PPM_ERROR]
    if client_settings.SATNOGS_IF_GAIN:
        args += ['--if-gain=' + client_settings.SATNOGS_IF_GAIN]
    if client_settings.SATNOGS_RF_GAIN:
        args += ['--rf-gain=' + client_settings.SATNOGS_RF_GAIN]
    if client_settings.SATNOGS_BB_GAIN:
        args += ['--bb-gain=' + client_settings.SATNOGS_BB_GAIN]
    if client_settings.SATNOGS_ANTENNA:
        args += ['--antenna=' + client_settings.SATNOGS_ANTENNA]
    if client_settings.SATNOGS_DEV_ARGS:
        args += ['--dev-args=' + client_settings.SATNOGS_DEV_ARGS]
    if client_settings.ENABLE_IQ_DUMP:
        args += ['--enable-iq-dump=' + str(int(client_settings.ENABLE_IQ_DUMP is True))]
    if client_settings.IQ_DUMP_FILENAME:
        args += ['--iq-file-path=' + client_settings.IQ_DUMP_FILENAME]
    if not client_settings.DISABLE_DECODED_DATA:
        args += ['--decoded-data-file-path=' + decoded_data]

    LOGGER.info('Starting GNUradio python script')
    proc = subprocess.Popen(args, preexec_fn=os.setsid)
    return proc
