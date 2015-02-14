from os import environ

GROUND_STATION_ID = int(environ.get('SATNOGS_STATION_ID', None))
SQLITE_URL = environ.get('SATNOGS_SQLITE_URL', 'sqlite:///jobs.sqlite')
DEMODULATION_COMMAND = environ.get('SATNOGS_DEMODULATION_COMMAND', 'rtl_fm')
ENCODING_COMMAND = environ.get('SATNOGS_ENCODING_COMMAND', 'oggenc')
DECODING_COMMAND = environ.get('SATNOGS_DECODING_COMMAND', 'multimon-ng')
OUTPUT_PATH = environ.get('SATNOGS_OUTPUT_PATH', '/tmp')
NETWORK_API_URL = environ.get('SATNOGS_API_URL', 'https://dev.satnogs.org/api/')
NETWORK_API_QUERY_INTERVAL = 5  # In minutes
SCHEDULER_SLEEP_TIME = 10  # In seconds
