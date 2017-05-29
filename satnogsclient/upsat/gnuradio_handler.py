import logging
import subprocess
import os

from satnogsclient import settings as client_settings

logger = logging.getLogger('default')


def exec_gnuradio(observation_file, waterfall_file, freq, user_args, script_name):
    arguments = {'filename': observation_file,
                 'waterfall': waterfall_file,
                 'rx_device': client_settings.SATNOGS_RX_DEVICE,
                 'center_freq': str(freq),
                 'ppm': client_settings.SATNOGS_PPM_ERROR,
                 'user_args': user_args,
                 'script_name': script_name}
    scriptname = arguments['script_name']
    doppler_correction = ''
    lo_offset = ''
    rigctl_port = ''
    rigctl_port = ''

    if not scriptname:
        scriptname = client_settings.GNURADIO_SCRIPT_FILENAME
    if user_args:
        if '--file-path=' in user_args:
            file_path = user_args.split('--file-path=')[1].split(' ')[0]
        elif '--file-path=' not in user_args:
            file_path = arguments['filename']
        if '--waterfall-file-path=' in user_args:
            waterfall_file_path = user_args.split('--waterfall-file-path=')[1].split(' ')[0]
        elif '--waterfall-file-path=' not in user_args:
            waterfall_file_path = arguments['waterfall']
        if '--ppm=' in user_args:
            ppm = user_args.split('--ppm=')[1].split(' ')[0]
        elif '--ppm=' not in user_args:
            ppm = str(arguments['ppm'])
        if '--rx-freq=' in user_args:
            rx_freq = user_args.split('--rx-freq=')[1].split(' ')[0]
        elif '--rx-freq=' not in user_args:
            rx_freq = arguments['center_freq']
        if '--rx-sdr-device=' in user_args:
            device = user_args.split('--rx-sdr-device=')[1].split(' ')[0]
        elif '--rx-sdr-device=' not in user_args:
            device = client_settings.SATNOGS_RX_DEVICE
        if '--doppler-correction-per-sec' in user_args:
            doppler_correction = '--doppler-correction-per-sec=' + user_args.split('--doppler-correction-per-sec=')[1].split(' ')[0] + ' '
        if '--doppler-correction-per-sec' in user_args:
            doppler_correction = '--doppler-correction-per-sec=' + user_args.split('--doppler-correction-per-sec=')[1].split(' ')[0] + ' '
        if '--lo-offset' in user_args:
            lo_offset = '--lo-offset=' + user_args.split('--lo-offset=')[1].split(' ')[0] + ' '
        if '--rigctl-port' in user_args:
            rigctl_port = '--rigctl-port=' + user_args.split('--rigctl-port=')[1].split(' ')[0] + ' '
    else:
        rx_freq = arguments['center_freq']
        device = client_settings.SATNOGS_RX_DEVICE
        file_path = arguments['filename']
        waterfall_file_path = arguments['waterfall']
        ppm = str(arguments['ppm'])

    arg_string = ' '
    arg_string += '--rx-sdr-device=' + device + ' '
    arg_string += '--rx-freq=' + rx_freq + ' '
    arg_string += '--file-path=' + file_path + ' '
    if scriptname != 'satnogs_generic_iq_receiver.py':
        arg_string += '--waterfall-file-path=' + waterfall_file_path + ' '
        arg_string += '--ppm=' + ppm + ' '
    arg_string += doppler_correction
    arg_string += lo_offset
    arg_string += rigctl_port

    logger.info('Starting GNUradio python script')
    proc = subprocess.Popen([scriptname + " " + arg_string], shell=True,
                            preexec_fn=os.setsid)
    return proc
