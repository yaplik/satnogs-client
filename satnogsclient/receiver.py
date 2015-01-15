import os

from datetime import datetime
from subprocess import Popen

import settings


class SignalSerializer():

    _decoding_values = [
        'POCSAG512',
        'POCSAG1200',
        'POCSAG2400',
        'EAS',
        'AFSK1200',
        'AFSK2400',
        'AFSK2400_2',
        'HAPN4800',
        'FSK9600',
        'DTMF',
        'ZVEI',
        'SCOPE'
    ]

    def __init__(self, observation_id, frequency, decoding, **kwargs):

        # Check input values
        if not observation_id:
            raise LookupError('arg not found: observation_id')
        if not frequency:
            raise LookupError('arg not found: frequency')

        if decoding not in self._decoding_values and decoding is not None:
            raise LookupError('arg not found: decoding')

        self.observation_id = observation_id
        self.frequency = frequency
        self.decoding = kwargs.get('decoding', None)
        self.ppm_error = kwargs.get('ppm_error', 100)
        self.demodulator = kwargs.get('demodulator', 'AFSK1200')
        self.modulation = kwargs.get('modulation', 'fm')
        self.sample_rate = kwargs.get('sample_rate', 22050)
        self.aprs = kwargs.get('aprs', True)

    def get_decoding_cmd(self):
        params = {
            '-t': 'raw',
            '-a': self.demodulator,
        }

        args = ['{0}{1}'.format(key, params[key]) for key in params]

        if self.aprs:
            args.append('-A')

        args.append('-')

        return [settings.DECODING_COMMAND] + args

    def get_demodulation_cmd(self):
        params = {
            '-f': self.frequency,
            '-p': self.ppm_error,
            '-s': self.sample_rate,
            '-M': self.modulation
        }

        args = ['{0} {1}'.format(key, params[key]) for key in params]

        return [settings.DEMODULATION_COMMAND] + args

    def get_output_path(self):
        timestamp = datetime.now().isoformat()
        filename = '{0}_{1}.out'.format(self.observation_id, timestamp)
        return os.path.join(settings.OUTPUT_PATH, filename)

    def run(self):
        self.pipe = os.pipe()
        self.output = open(self.get_output_path(), 'w')

        self.consumer = Popen(self.get_decoding_cmd(), stdin=self.pipe[0])
        self.producer = Popen(self.get_demodulation_cmd(), stdout=self.pipe[1])

        self.consumer.wait()
        self.producer.wait()

    def stop(self):
        self.consumer.kill()
        self.producer.kill()
        self.output.close()
        self.pipe[0].close()
        self.pipe[1].close()
