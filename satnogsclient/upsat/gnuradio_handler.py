from __future__ import absolute_import, division, print_function

import json
import logging
import subprocess

from satnogsclient import settings as client_settings

LOGGER = logging.getLogger(__name__)


def get_gnuradio_info():
    process = subprocess.Popen(['python3', '-m', 'satnogs.satnogs_info'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    gr_satnogs_info, _ = process.communicate()  # pylint: disable=W0612
    client_metadata = {
        'radio': {
            'name': 'gr-satnogs',
            'version': None,
            'rx_device': client_settings.SATNOGS_SOAPY_RX_DEVICE,
            'samp_rate': client_settings.SATNOGS_RX_SAMP_RATE,
            'bandwidth': client_settings.SATNOGS_RX_BANDWIDTH,
            'gain_mode': client_settings.SATNOGS_GAIN_MODE,
            'rf_gain': client_settings.SATNOGS_RF_GAIN,
            'antenna': client_settings.SATNOGS_ANTENNA,
            'lo_offset': client_settings.SATNOGS_LO_OFFSET,
            'ppm_error': client_settings.SATNOGS_PPM_ERROR,
            'dev_args': client_settings.SATNOGS_DEV_ARGS,
            'stream_args': client_settings.SATNOGS_STREAM_ARGS,
            'tune_args': client_settings.SATNOGS_TUNE_ARGS,
            'other_settings': client_settings.SATNOGS_OTHER_SETTINGS,
            'dc_removal': client_settings.SATNOGS_DC_REMOVAL,
            'bb_freq': client_settings.SATNOGS_BB_FREQ,
        }
    }
    if process.returncode == 0:
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


def get_flowgraph_script_name(mode=''):
    """
    Returns the GNU Radio flowgraph script name that will be executed based on the
    given mode, or the default one if no mode is specified
    """
    if mode not in client_settings.SATNOGS_FLOWGRAPHS:
        return client_settings.GNURADIO_DEFAULT_SCRIPT_FILENAME
    return client_settings.SATNOGS_FLOWGRAPHS[mode]['script_name']


def exec_gnuradio(observation_file, waterfall_file, freq, mode, baud, decoded_data):
    args = [
        get_flowgraph_script_name(mode),
        '--soapy-rx-device=' + client_settings.SATNOGS_SOAPY_RX_DEVICE,
        '--samp-rate-rx=' + str(client_settings.SATNOGS_RX_SAMP_RATE), '--rx-freq=' + str(freq),
        '--file-path=' + observation_file
    ]

    if waterfall_file != '':
        args += ['--waterfall-file-path=' + waterfall_file]

    # Apply baudrate on the supported flowgraphs
    if mode in client_settings.SATNOGS_FLOWGRAPHS and baud and client_settings.SATNOGS_FLOWGRAPHS[
            mode]['has_baudrate']:
        # If this is a CW observation pass the WPM parameter
        if mode == 'CW':
            args += ['--wpm=' + str(int(baud))]
        else:
            args += ['--baudrate=' + str(int(baud))]

    # Apply framing mode
    if mode in client_settings.SATNOGS_FLOWGRAPHS and client_settings.SATNOGS_FLOWGRAPHS[mode][
            'has_framing']:
        args += ['--framing=' + client_settings.SATNOGS_FLOWGRAPHS[mode]['framing']]

    if client_settings.SATNOGS_DOPPLER_CORR_PER_SEC:
        args += ['--doppler-correction-per-sec=' + client_settings.SATNOGS_DOPPLER_CORR_PER_SEC]
    if client_settings.SATNOGS_LO_OFFSET:
        args += ['--lo-offset=' + client_settings.SATNOGS_LO_OFFSET]
    if client_settings.SATNOGS_PPM_ERROR:
        args += ['--ppm=' + client_settings.SATNOGS_PPM_ERROR]
    if client_settings.SATNOGS_RIG_PORT:
        args += ['--rigctl-port=' + str(client_settings.SATNOGS_RIG_PORT)]
    if client_settings.SATNOGS_GAIN_MODE:
        args += ['--gain-mode=' + client_settings.SATNOGS_GAIN_MODE]
    if client_settings.SATNOGS_RF_GAIN:
        args += ['--gain=' + client_settings.SATNOGS_RF_GAIN]
    if client_settings.SATNOGS_ANTENNA:
        args += ['--antenna=' + client_settings.SATNOGS_ANTENNA]
    if client_settings.SATNOGS_DEV_ARGS:
        args += ['--dev-args=' + client_settings.SATNOGS_DEV_ARGS]
    if client_settings.SATNOGS_STREAM_ARGS:
        args += ['--stream-args=' + client_settings.SATNOGS_STREAM_ARGS]
    if client_settings.SATNOGS_TUNE_ARGS:
        args += ['--tune-args=' + client_settings.SATNOGS_TUNE_ARGS]
    if client_settings.SATNOGS_OTHER_SETTINGS:
        args += ['--other-settings=' + client_settings.SATNOGS_OTHER_SETTINGS]
    if client_settings.SATNOGS_DC_REMOVAL:
        args += ['--dc-removal=' + client_settings.SATNOGS_DC_REMOVAL]
    if client_settings.SATNOGS_BB_FREQ:
        args += ['--bb-freq=' + client_settings.SATNOGS_BB_FREQ]
    if client_settings.SATNOGS_RX_BANDWIDTH:
        args += ['--bw=' + client_settings.SATNOGS_RX_BANDWIDTH]
    if client_settings.ENABLE_IQ_DUMP:
        args += ['--enable-iq-dump=' + str(int(client_settings.ENABLE_IQ_DUMP is True))]
    if client_settings.IQ_DUMP_FILENAME:
        args += ['--iq-file-path=' + client_settings.IQ_DUMP_FILENAME]
    if not client_settings.DISABLE_DECODED_DATA:
        args += ['--decoded-data-file-path=' + decoded_data]

    LOGGER.info('Starting GNUradio python script')
    try:
        proc = subprocess.Popen(args)
        return proc
    except OSError:
        LOGGER.exception('Could not start GNURadio python script')

    return None
