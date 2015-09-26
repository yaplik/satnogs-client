# -*- coding: utf-8 -*-
import logging
import os

from datetime import datetime
from subprocess import Popen

import settings


logger = logging.getLogger('satnogsclient')


class SignalReceiver():

    _decoding_values = [
        'POCSAG512',
        'POCSAG1200',
        'POCSAG2400',
        'EAS',
        'UFSK1200',
        'CLIPFSK',
        'FMSFSK',
        'AFSK1200',
        'AFSK2400',
        'AFSK2400_2',
        'AFSK2400_3',
        'HAPN4800',
        'FSK9600',
        'DTMF',
        'ZVEI1',
        'ZVEI2',
        'ZVEI3',
        'DZVEI',
        'PZVEI',
        'EEA',
        'EIA',
        'CCIR',
        'MORSE_CW',
        'DUMPCSV',
        'SCOPE'
    ]

    def __init__(self, observation_id, frequency, decoding=None, **kwargs):
        """Initialises receiver"""

        # Check input values
        # We need the observation_id so that it accompanies the serialised output
        if not observation_id:
            raise LookupError('arg not found: observation_id')

        # Frequency is needed to pass to rtl_fm
        if not frequency:
            raise LookupError('arg not found: frequency')

        # Decoding can be None or any value in _decoding_values
        if decoding not in self._decoding_values and decoding is not None:
            raise LookupError('arg not found: decoding')

        # Initialise attributes and default values
        self.observation_id = observation_id
        self.frequency = frequency
        self.decoding = kwargs.get('decoding', None)
        self.ppm_error = settings.PPM_ERROR  # sliding error of receiver
        self.pcm_demodulator = kwargs.get('demodulator', 'AFSK1200')
        self.modulation = kwargs.get('modulation', 'fm')  # mode of received signal
        self.sample_rate = kwargs.get('sample_rate', 22050)  # sample rate for rtl_fm output

        # If aprs is True, multimon-ng sets pcm_demodulator to 'AFSK1200' automagically
        self.aprs = kwargs.get('aprs', True)

    def get_decoding_cmd(self):
        """Provides decoding command."""
        if self.decoding:
            params = {
                '-t': 'raw',  # always raw
                '-a': self.pcm_demodulator,
            }

            args = []
            for key in params:
                args.append(key)
                args.append(params[key])

            if self.aprs:
                args.append('-A')

            args.append('-')
            cmd = [settings.ENCODING_COMMAND] + args
        else:
            # oggenc --raw-endianess=0 -R 24k -B 16 -C 1 -r -q 4
            params = {
                '-R': '24000',
                '-B': '16',
                '-C': '1',
                '-q': '4'
            }
            args = ['--raw-endianness=0', '-r']
            for key in params:
                args.append(key)
                args.append(params[key])

            args.append('-')
            cmd = [settings.ENCODING_COMMAND] + args
        return cmd

    def get_demodulation_cmd(self):
        """Provides demodulation command."""
        if settings.HARDWARE_RADIO:
            params = {
                '-f': 'cd',
                '-t': 'raw'
            }
        else:
            params = {
                '-f': self.frequency,
                '-p': self.ppm_error,
                '-s': self.sample_rate,
                '-M': self.modulation,
                '-g': '40'
            }

        args = []
        for key in params:
            args.append(key)
            args.append(params[key])

        return [settings.DEMODULATION_COMMAND] + args

    def get_output_path(self, receiving=True):
        """Provides path to observation output file."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S%z')
        file_extension = 'out' if self.decoding else 'ogg'
        if receiving:
            prefix = 'receiving_satnogs'
        else:
            prefix = 'satnogs'
        filename = '{0}_{1}_{2}.{3}'.format(prefix, self.observation_id, timestamp, file_extension)
        return os.path.join(settings.OUTPUT_PATH, filename)

    def run(self):
        """Runs the receiver. Orchestrates data piping between precompiled utilities."""
        logger.info('Initiate receiver')
        self.pipe = os.pipe()
        self.output = open(self.get_output_path(), 'w')

        self.consumer = Popen(self.get_decoding_cmd(), stdin=self.pipe[0], stdout=self.output)
        self.producer = Popen(self.get_demodulation_cmd(), stdout=self.pipe[1])

    def stop(self):
        """Stops the receiver pipelines."""
        logger.info('Stop receiver')
        filename = self.get_output_path(receiving=False)
        os.rename(self.output.name, filename)
        self.producer.kill()
        self.consumer.kill()
        self.output.close()
        os.close(self.pipe[0])
        os.close(self.pipe[1])
