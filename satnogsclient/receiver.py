# -*- coding: utf-8 -*-
import os

from datetime import datetime
from subprocess import Popen

import settings


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
        """ Initialises receiver """

        ##  Check input values

        # we need the observation_id so that it accompanies the serialised output
        if not observation_id:
            raise LookupError('arg not found: observation_id')
        # frequency is needed to pass to rtl_fm
        if not frequency:
            raise LookupError('arg not found: frequency')

        # decoding can be None (PCM encoding/compression) or any predefined value (multmon-ng decoding)
        if decoding not in self._decoding_values and decoding is not None:
            raise LookupError('arg not found: decoding')

        ## Initialise variables
        self.observation_id = observation_id
        self.frequency = frequency
        self.decoding = kwargs.get('decoding', None)
        self.ppm_error = kwargs.get('ppm_error', 100)  # sliding error of receiver. It is normally "about" 100. Part of calibration
        self.pcm_demodulator = kwargs.get('demodulator', 'AFSK1200')  # demodulation of pcm in order to get decoded
        self.modulation = kwargs.get('modulation', 'fm')  # mode of received signal
        self.sample_rate = kwargs.get('sample_rate', 22050)  # sample rate of wav file produced by rtl_fm
        self.aprs = kwargs.get('aprs', True)  # APRS: final decoding format (only available
        ## NOTE: if aprs is True, multimon-ng sets pcm_demodulator to 'AFSK1200' automagically

    def get_decoding_cmd(self):
        """ Provides decoding command."""
        if self.decoding:
            params = {
                '-t': 'raw',  # always raw
                '-a': self.pcm_demodulator,
            }

            args = ['{0}{1}'.format(key, params[key]) for key in params]

            if self.aprs:
                args.append('-A')

            args.append('-')
            ret = [settings.ENCODING_COMMAND] + args
        else:
            # oggenc --raw-endianess=0 -R 24k -B 16 -C 1 -r -q 4
            params = {
                '-R': '24000',
                '-B': '16',
                '-C': '1',
                '-q': '4'
            }
            args = ['--raw-endianness=0', '-r']
            args += ['{0} {1}'.format(key, params[key]) for key in params]
            args += ['-']
            ret = [settings.ENCODING_COMMAND] + args
        return ret

    def get_demodulation_cmd(self):
        """ Provides decoding command."""
        params = {
            '-f': self.frequency,
            '-p': self.ppm_error,
            '-s': self.sample_rate,
            '-M': self.modulation
        }
        args = ['{0} {1}'.format(key, params[key]) for key in params]
        return [settings.DEMODULATION_COMMAND] + args

    def get_output_path(self):
        """ Provides output path for serialisation of output."""
        timestamp = datetime.utcnow().isoformat()
        file_extension = 'ogg' if self.decoding else 'out'
        filename = 'satnogs_{0}_{1}.{2}'.format(self.observation_id, timestamp, file_extension)
        return os.path.join(settings.OUTPUT_PATH, filename)

    def run(self):
        """ Runs the receiver. Orchestrates data piping between precompiled utilities. """
        self.pipe = os.pipe()
        self.output = open(self.get_output_path(), 'w')

        self.consumer = Popen(self.get_decoding_cmd(), stdin=self.pipe[0], stdout=self.output)
        self.producer = Popen(self.get_demodulation_cmd(), stdout=self.pipe[1])

    def stop(self):
        """ Stops the receiver pipelines."""
        self.producer.kill()
        self.consumer.kill()
        self.output.close()
        os.close(self.pipe[0])
        os.close(self.pipe[1])
