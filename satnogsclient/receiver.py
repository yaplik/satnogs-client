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

    def __init__(self, observation_id, frequency, decoding=None):

        # Check input values
        if not observation_id:
            raise LookupError('arg not found: observation_id')
        if not frequency:
            raise LookupError('arg not found: frequency')

        if decoding not in self._decoding_values and decoding not None:
            raise LookupError('arg not found: decoding')

        self.observation_id = observation_id
        self.frequency = frequency
        self.decoding = decoding

    def get_decoding_cmd(self):
        raise NotImplementedError()

    def get_demodulation_cmd(self):
        raise NotImplementedError()

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
