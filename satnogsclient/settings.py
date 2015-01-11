from os import environ

DEMODULATION_COMMAND = environ.get('DEMODULATION_COMMAND', None)
ENCODING_COMMAND = environ.get('ENCODING_COMMAND', None)
DECODING_COMMAND = environ.get('DECODING_COMMAND', None)
OUTPUT_PATH = environ.get('OUTPUT_PATH', None)
