from __future__ import absolute_import, division, print_function

import json
import logging
import os
import shlex
import signal
import subprocess
from datetime import datetime
from time import sleep

import pytz
import requests

import satnogsclient.config
from satnogsclient import settings
from satnogsclient.observer.waterfall import plot_waterfall
from satnogsclient.observer.worker import WorkerFreq, WorkerTrack
from satnogsclient.upsat import gnuradio_handler

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

LOGGER = logging.getLogger(__name__)


class Observer(object):

    _gnu_proc = None

    # Variables from settings
    # Mainly present so we can support multiple ground stations from the client

    def __init__(self):
        self.location = None
        self.rot_ip = settings.SATNOGS_ROT_IP
        self.rot_port = settings.SATNOGS_ROT_PORT
        self.rig_ip = settings.SATNOGS_RIG_IP
        self.rig_port = settings.SATNOGS_RIG_PORT
        self.observation_id = None
        self.tle = None
        self.timestamp = None
        self.observation_end = None
        self.frequency = None
        self.observation_raw_file = None
        self.observation_ogg_file = None
        self.observation_waterfall_file = None
        self.observation_waterfall_png = None
        self.observation_receiving_decoded_data = None  # pylint: disable=C0103
        self.observation_decoded_data = None
        self.baud = None
        self.observation_done_decoded_data = None
        self.tracker_freq = None
        self.tracker_rot = None
        self.script_name = None

    def setup(self, observation_id, tle, observation_end, frequency, baud, script_name):
        """
        Sets up required internal variables.
        * returns True if setup is ok
        * returns False if issue is encountered
        """

        # Set attributes
        self.observation_id = observation_id
        self.script_name = script_name
        self.tle = tle
        self.observation_end = observation_end
        self.frequency = frequency
        self.baud = baud

        not_completed_prefix = 'receiving_satnogs'
        completed_prefix = 'satnogs'
        receiving_waterfall_prefix = 'receiving_waterfall'
        waterfall_prefix = 'waterfall'
        receiving_decoded_data_prefix = 'receiving_data'
        decoded_data_prefix = 'data'
        self.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S%z')
        raw_file_extension = 'out'
        encoded_file_extension = 'ogg'
        waterfall_file_extension = 'dat'
        self.observation_raw_file = '{0}/{1}_{2}_{3}.{4}'.format(settings.SATNOGS_OUTPUT_PATH,
                                                                 not_completed_prefix,
                                                                 self.observation_id,
                                                                 self.timestamp,
                                                                 raw_file_extension)
        self.observation_ogg_file = '{0}/{1}_{2}_{3}.{4}'.format(settings.SATNOGS_OUTPUT_PATH,
                                                                 completed_prefix,
                                                                 self.observation_id,
                                                                 self.timestamp,
                                                                 encoded_file_extension)
        self.observation_waterfall_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH, receiving_waterfall_prefix, self.observation_id,
            self.timestamp, waterfall_file_extension)
        self.observation_waterfall_png = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH, waterfall_prefix, self.observation_id, self.timestamp,
            'png')
        self.observation_receiving_decoded_data = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH, receiving_decoded_data_prefix, self.observation_id,
            self.timestamp, 'png')
        self.observation_done_decoded_data = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH, decoded_data_prefix, self.observation_id, self.timestamp,
            'png')
        self.observation_decoded_data = '{0}/{1}_{2}'.format(settings.SATNOGS_OUTPUT_PATH,
                                                             decoded_data_prefix,
                                                             self.observation_id)
        return all([
            self.observation_id, self.tle, self.timestamp, self.observation_end, self.frequency,
            self.observation_raw_file, self.observation_ogg_file, self.observation_waterfall_file,
            self.observation_waterfall_png, self.observation_decoded_data
        ])

    def observe(self):
        """Starts threads for rotcrl and rigctl."""
        if settings.SATNOGS_PRE_OBSERVATION_SCRIPT is not None:
            LOGGER.info('Executing pre-observation script.')
            replacements = [
                ("{{FREQ}}", str(self.frequency)),
                ("{{TLE}}", json.dumps(self.tle)),
                ("{{TIMESTAMP}}", self.timestamp),
                ("{{ID}}", str(self.observation_id)),
                ("{{BAUD}}", str(self.baud)),
                ("{{SCRIPT_NAME}}", self.script_name),
            ]
            pre_script = []
            for arg in shlex.split(settings.SATNOGS_PRE_OBSERVATION_SCRIPT):
                for key, val in replacements:
                    arg = arg.replace(key, val)
                pre_script.append(arg)
            subprocess.call(pre_script)

        # if it is APT we want to save with a prefix until the observation
        # is complete, then rename.
        if settings.GNURADIO_APT_SCRIPT_FILENAME in self.script_name:
            self.observation_decoded_data =\
                 self.observation_receiving_decoded_data

        # start thread for rotctl
        LOGGER.info('Start rotctrl thread.')
        self.run_rot()
        # start thread for rigctl
        LOGGER.info('Start rigctrl thread.')
        self.run_rig()
        sleep(1)
        LOGGER.info('Start gnuradio thread.')
        self._gnu_proc = gnuradio_handler.exec_gnuradio(self.observation_raw_file,
                                                        self.observation_waterfall_file,
                                                        self.frequency, self.baud,
                                                        self.script_name,
                                                        self.observation_decoded_data)
        # Polling gnuradio process status
        self.poll_gnu_proc_status()

        if "satnogs_generic_iq_receiver.py" not in settings.GNURADIO_SCRIPT_FILENAME:
            LOGGER.info('Rename encoded files for uploading.')
            self.rename_ogg_file()
            self.rename_data_file()
            LOGGER.info('Creating waterfall plot.')
            self.plot_waterfall()

        # PUT client version and metadata
        base_url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'observations/')
        headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}
        url = urljoin(base_url, str(self.observation_id))
        if not url.endswith('/'):
            url += '/'
        client_metadata = gnuradio_handler.get_gnuradio_info()
        client_metadata['latitude'] = settings.SATNOGS_STATION_LAT
        client_metadata['longitude'] = settings.SATNOGS_STATION_LON
        client_metadata['elevation'] = settings.SATNOGS_STATION_ELEV
        client_metadata['frequency'] = self.frequency

        try:
            resp = requests.put(url,
                                headers=headers,
                                data={
                                    'client_version': satnogsclient.config.VERSION,
                                    'client_metadata': json.dumps(client_metadata)
                                },
                                verify=settings.SATNOGS_VERIFY_SSL,
                                stream=True,
                                timeout=45)
        except requests.exceptions.ConnectionError:
            LOGGER.error('%s: Connection Refused', url)
        except requests.exceptions.Timeout:
            LOGGER.error('%s: Connection Timeout - no metadata uploaded', url)
        except requests.exceptions.RequestException as err:
            LOGGER.error('%s: Unexpected error: %s', url, err)

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as http_error:
            LOGGER.error(http_error)

    def run_rot(self):
        self.tracker_rot = WorkerTrack(ip=self.rot_ip,
                                       port=self.rot_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end,
                                       proc=self._gnu_proc,
                                       sleep_time=3)
        LOGGER.debug('TLE: %s', self.tle)
        LOGGER.debug('Observation end: %s', self.observation_end)
        self.tracker_rot.trackobject(self.location, self.tle)
        self.tracker_rot.trackstart()

    def run_rig(self):
        self.tracker_freq = WorkerFreq(ip=self.rig_ip,
                                       port=self.rig_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end,
                                       proc=self._gnu_proc)
        LOGGER.debug('Rig Frequency %s', self.frequency)
        LOGGER.debug('Observation end: %s', self.observation_end)
        self.tracker_freq.trackobject(self.location, self.tle)
        self.tracker_freq.trackstart()

    def poll_gnu_proc_status(self):
        while self._gnu_proc.poll() is None and datetime.now(pytz.utc) <= self.observation_end:
            sleep(1)
        LOGGER.info('Tracking stopped.')
        self._gnu_proc.send_signal(signal.SIGINT)
        _, _ = self._gnu_proc.communicate()
        self.tracker_freq.trackstop()
        self.tracker_rot.trackstop()
        LOGGER.info('Observation Finished')
        LOGGER.info('Executing post-observation script.')
        if settings.SATNOGS_POST_OBSERVATION_SCRIPT is not None:
            replacements = [
                ("{{FREQ}}", str(self.frequency)),
                ("{{TLE}}", json.dumps(self.tle)),
                ("{{TIMESTAMP}}", self.timestamp),
                ("{{ID}}", str(self.observation_id)),
                ("{{BAUD}}", str(self.baud)),
                ("{{SCRIPT_NAME}}", self.script_name),
            ]
            post_script = []
            for arg in shlex.split(settings.SATNOGS_POST_OBSERVATION_SCRIPT):
                for key, val in replacements:
                    arg = arg.replace(key, val)
                post_script.append(arg)
            subprocess.call(post_script)

    def rename_ogg_file(self):
        if os.path.isfile(self.observation_raw_file):
            os.rename(self.observation_raw_file, self.observation_ogg_file)
        LOGGER.info('Rename encoded file for uploading finished')

    def rename_data_file(self):
        if os.path.isfile(self.observation_receiving_decoded_data):
            os.rename(self.observation_receiving_decoded_data, self.observation_done_decoded_data)
        LOGGER.info('Rename data file for uploading finished')

    def plot_waterfall(self):
        if os.path.isfile(self.observation_waterfall_file):
            plot_waterfall(waterfall_file=self.observation_waterfall_file,
                           waterfall_png=self.observation_waterfall_png)
            if os.path.isfile(self.observation_waterfall_png) and \
               settings.SATNOGS_REMOVE_RAW_FILES:
                self.remove_waterfall_file()
        else:
            LOGGER.error('No waterfall data file found')

    def remove_waterfall_file(self):
        if os.path.isfile(self.observation_waterfall_file):
            os.remove(self.observation_waterfall_file)
