import logging
import subprocess
import os

from satnogsclient import settings as client_settings

logger = logging.getLogger('default')


def exec_gnuradio(observation_file, waterfall_file, origin, freq, baud,
                  user_args, script_name, decoded_data):
    arguments = {'filename': observation_file,
                 'waterfall': waterfall_file,
                 'rx_device': client_settings.SATNOGS_RX_DEVICE,
                 'center_freq': str(freq),
                 'user_args': user_args,
                 'script_name': script_name,
                 'decoded_data': decoded_data}
    scriptname = arguments['script_name']
    arg_string = ' '
    if not scriptname:
        scriptname = client_settings.GNURADIO_SCRIPT_FILENAME
    if origin == 'network':
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
            arg_string += '--wpm=' + str(baud) + ' '
    else:
        arg_string = user_args + ' '
    if client_settings.SATNOGS_RX_DEVICE and "--rx-sdr-device" not in arg_string:
        arg_string += '--rx-sdr-device=' + client_settings.SATNOGS_RX_DEVICE + ' '
    if client_settings.SATNOGS_DOPPLER_CORR_PER_SEC and "--doppler-correction-per-sec" not in arg_string:
        arg_string += '--doppler-correction-per-sec=' + client_settings.SATNOGS_DOPPLER_CORR_PER_SEC + ' '
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
        arg_string += '--enable-iq-dump=' + client_settings.ENABLE_IQ_DUMP + ' '
    if client_settings.IQ_DUMP_FILENAME and "--iq-file-path" not in arg_string:
        arg_string += '--iq-file-path=' + client_settings.IQ_DUMP_FILENAME + ' '
    if not client_settings.DISABLE_DECODED_DATA and "--decoded-data-file-path" not in arg_string:
        arg_string += '--decoded-data-file-path=' + arguments['decoded_data'] + ' '

    logger.info('Starting GNUradio python script')
    proc = subprocess.Popen([scriptname + " " + arg_string], shell=True,
                            preexec_fn=os.setsid)
    return proc
