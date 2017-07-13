import logging
import subprocess
import os

from satnogsclient import settings as client_settings

logger = logging.getLogger('default')


def exec_gnuradio(observation_file, waterfall_file, origin, freq, user_args, script_name):
    arguments = {'filename': observation_file,
                 'waterfall': waterfall_file,
                 'rx_device': client_settings.SATNOGS_RX_DEVICE,
                 'center_freq': str(freq),
                 'ppm': client_settings.SATNOGS_PPM_ERROR,
                 'user_args': user_args,
                 'script_name': script_name}
    scriptname = arguments['script_name']
    arg_string = ' '
    if not scriptname:
        scriptname = client_settings.GNURADIO_SCRIPT_FILENAME
    if origin == 'network':
        rx_freq = arguments['center_freq']
        device = client_settings.SATNOGS_RX_DEVICE
        file_path = arguments['filename']
        waterfall_file_path = arguments['waterfall']
        ppm = str(arguments['ppm'])
        arg_string += '--rx-sdr-device=' + device + ' '
        arg_string += '--rx-freq=' + rx_freq + ' '
        arg_string += '--file-path=' + file_path + ' '
        arg_string += '--ppm=' + ppm + ' '
        if arguments['waterfall'] != "":
            arg_string += '--waterfall-file-path=' + waterfall_file_path + ' '
    else:
        arg_string = user_args

    logger.info('Starting GNUradio python script')
    proc = subprocess.Popen([scriptname + " " + arg_string], shell=True,
                            preexec_fn=os.setsid)
    return proc
