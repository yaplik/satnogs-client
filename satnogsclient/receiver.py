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

        if decoding not in self._decoding_values or decoding is not None:
            raise LookupError('arg not found: decoding')

        self.observation_id = observation_id
        self.frequency = frequency
        self.decoding = decoding

    def run(self):
        raise NotImplementedError
