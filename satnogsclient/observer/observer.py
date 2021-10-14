from __future__ import absolute_import, division, print_function

import json
import logging
import shlex
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from time import sleep

import pytz
import requests

import satnogsclient.config
import satnogsclient.radio.flowgraphs as flowgraphs
from satnogsclient import settings
from satnogsclient.artifacts import Artifacts
from satnogsclient.observer.worker import WorkerFreq, WorkerTrack
from satnogsclient.scheduler import SCHEDULER
from satnogsclient.waterfall import EmptyArrayError, Waterfall

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

LOGGER = logging.getLogger(__name__)


def post_artifacts(artifacts_file, observation_id):
    url = urljoin(settings.ARTIFACTS_API_URL, 'artifacts/')
    headers = {'Authorization': 'Token {0}'.format(settings.ARTIFACTS_API_TOKEN)}
    if not url.endswith('/'):
        url += '/'

    try:
        response = requests.post(url,
                                 headers=headers,
                                 files={
                                     'artifact_file': (str(uuid.uuid4()) + '.h5', artifacts_file,
                                                       'application/x-hdf5')
                                 },
                                 verify=settings.SATNOGS_VERIFY_SSL,
                                 stream=True,
                                 timeout=settings.ARTIFACTS_API_TIMEOUT)
        response.raise_for_status()

        LOGGER.info('Artifacts upload successful.')
        artifacts_file.close()

    except requests.exceptions.Timeout:
        LOGGER.error('Upload of artifacts for observation %s failed '
                     'due to timeout.', observation_id)
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            LOGGER.error(
                "Upload of artifacts for observation %s failed, %s doesn't exist (404)."
                'Probably the observation was deleted.', observation_id, url)

        if response.status_code == 403 and 'has already been uploaded' in response.text:
            LOGGER.error('Upload of artifacts for observation %s is forbidden, %s\n URL: %s',
                         observation_id, response.text, url)
        else:
            LOGGER.error(
                'Upload of artifacts for observation %s failed, '
                'response status code: %s', observation_id, response.status_code)


class Observer(object):

    # Variables from settings
    # Mainly present so we can support multiple ground stations from the client

    def __init__(self):
        self.location = None
        self.rot_port = settings.SATNOGS_ROT_PORT
        self.rig_ip = settings.SATNOGS_RIG_IP
        self.rig_port = settings.SATNOGS_RIG_PORT
        self.observation_id = None
        self.tle = None
        self.timestamp = None
        self.observation_end = None
        self.frequency = None
        self.mode = None
        self.baud = None
        self.observation_raw_file = None
        self.observation_ogg_file = None
        self.observation_waterfall_file = None
        self.observation_waterfall_png = None
        self.observation_receiving_decoded_data = None  # pylint: disable=C0103
        self.observation_decoded_data = None
        self.observation_done_decoded_data = None
        self.tracker_freq = None
        self.tracker_rot = None

    def setup(self, observation_id, tle, observation_end, frequency, mode, baud):
        """
        Sets up required internal variables.
        * returns True if setup is ok
        * returns False if issue is encountered
        """

        # Set attributes
        self.observation_id = observation_id
        self.tle = tle
        self.observation_end = observation_end
        self.frequency = frequency
        self.baud = baud
        self.mode = mode

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

    def observe(self):  # pylint: disable=R0915
        """Starts threads for rotcrl and rigctl."""
        if settings.SATNOGS_PRE_OBSERVATION_SCRIPT is not None:
            LOGGER.info('Executing pre-observation script.')

            script_name = flowgraphs.SATNOGS_FLOWGRAPH_MODES[
                flowgraphs.SATNOGS_FLOWGRAPH_MODE_DEFAULT]['script_name']
            if self.mode in flowgraphs.SATNOGS_FLOWGRAPH_MODES:
                script_name = flowgraphs.SATNOGS_FLOWGRAPH_MODES[self.mode]['script_name']

            replacements = [
                ('{{FREQ}}', str(self.frequency)),
                ('{{TLE}}', json.dumps(self.tle)),
                ('{{TIMESTAMP}}', self.timestamp),
                ('{{ID}}', str(self.observation_id)),
                ('{{BAUD}}', str(self.baud)),
                ('{{SCRIPT_NAME}}', script_name),
            ]
            pre_script = []
            for arg in shlex.split(settings.SATNOGS_PRE_OBSERVATION_SCRIPT):
                for key, val in replacements:
                    arg = arg.replace(key, val)
                pre_script.append(arg)
            subprocess.call(pre_script)

        # if it is APT we want to save with a prefix until the observation
        # is complete, then rename.
        if self.mode == 'APT':
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
        flowgraph = satnogsclient.radio.flowgraphs.Flowgraph(
            settings.SATNOGS_SOAPY_RX_DEVICE, settings.SATNOGS_RX_SAMP_RATE, self.frequency,
            self.mode, self.baud, {
                'audio': self.observation_raw_file,
                'waterfall': self.observation_waterfall_file,
                'decoded': self.observation_decoded_data
            })
        flowgraph.enabled = True
        # Polling gnuradio process status
        self.poll_gnu_proc_status(flowgraph)

        # Rename files and create waterfall
        self.rename_ogg_file()
        self.rename_data_file()
        LOGGER.info('Creating waterfall plot.')
        waterfall = None
        try:
            waterfall = Waterfall(self.observation_waterfall_file)
            self.plot_waterfall(waterfall)
            if settings.SATNOGS_REMOVE_RAW_FILES:
                self.remove_waterfall_file()
        except FileNotFoundError:
            LOGGER.error('No waterfall data file found')
        except EmptyArrayError:
            LOGGER.error('Waterfall data array is empty')

        # PUT client version and metadata
        base_url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'observations/')
        headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}
        url = urljoin(base_url, str(self.observation_id))
        if not url.endswith('/'):
            url += '/'
        client_metadata = flowgraph.info
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
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            LOGGER.error('%s: Connection Refused', url)
        except requests.exceptions.Timeout:
            LOGGER.error('%s: Connection Timeout - no metadata uploaded', url)
        except requests.exceptions.HTTPError as http_error:
            LOGGER.error(http_error)
        except requests.exceptions.RequestException as err:
            LOGGER.error('%s: Unexpected error: %s', url, err)

        if settings.ARTIFACTS_ENABLED:
            metadata = {
                'observation_id': self.observation_id,
                'frequency': str(self.frequency),
                'tle': '{}\n{}\n{}\n'.format(self.tle['tle0'], self.tle['tle1'], self.tle['tle2']),
                'location': {
                    'latitude': self.location['lat'],
                    'longitude': self.location['lon'],
                    'altitude': self.location['elev']
                }
            }
            artifact = Artifacts(waterfall, metadata)
            artifact.create()
            SCHEDULER.add_job(post_artifacts,
                              args=(artifact.artifacts_file, str(self.observation_id)))

    def run_rot(self):
        self.tracker_rot = WorkerTrack(port=self.rot_port,
                                       time_to_stop=self.observation_end,
                                       sleep_time=3)
        LOGGER.debug('TLE: %s', self.tle)
        LOGGER.debug('Observation end: %s', self.observation_end)
        self.tracker_rot.trackobject(self.location, self.tle)
        self.tracker_rot.trackstart()

    def run_rig(self):
        self.tracker_freq = WorkerFreq(ip=self.rig_ip,
                                       port=self.rig_port,
                                       time_to_stop=self.observation_end)
        LOGGER.debug('Rig Frequency %s', self.frequency)
        LOGGER.debug('Observation end: %s', self.observation_end)
        self.tracker_freq.trackobject(self.frequency, self.location, self.tle)
        self.tracker_freq.trackstart()

    def poll_gnu_proc_status(self, flowgraph):
        while flowgraph.enabled and datetime.now(pytz.utc) <= self.observation_end:
            sleep(1)
        flowgraph.enabled = False
        LOGGER.info('Tracking stopped.')
        self.tracker_freq.trackstop()
        self.tracker_rot.trackstop()
        LOGGER.info('Observation Finished')
        LOGGER.info('Executing post-observation script.')
        if settings.SATNOGS_POST_OBSERVATION_SCRIPT is not None:

            script_name = flowgraphs.SATNOGS_FLOWGRAPH_MODES[
                flowgraphs.SATNOGS_FLOWGRAPH_MODE_DEFAULT]['script_name']
            if self.mode in flowgraphs.SATNOGS_FLOWGRAPH_MODES:
                script_name = flowgraphs.SATNOGS_FLOWGRAPH_MODES[self.mode]['script_name']

            replacements = [
                ('{{FREQ}}', str(self.frequency)),
                ('{{TLE}}', json.dumps(self.tle)),
                ('{{TIMESTAMP}}', self.timestamp),
                ('{{ID}}', str(self.observation_id)),
                ('{{BAUD}}', str(self.baud)),
                ('{{SCRIPT_NAME}}', script_name),
            ]
            post_script = []
            for arg in shlex.split(settings.SATNOGS_POST_OBSERVATION_SCRIPT):
                for key, val in replacements:
                    arg = arg.replace(key, val)
                post_script.append(arg)
            subprocess.call(post_script)

    def rename_ogg_file(self):
        observation_raw_file_path = Path(self.observation_raw_file)
        if observation_raw_file_path.exists():
            observation_raw_file_path.rename(Path(self.observation_ogg_file))
            LOGGER.info('Rename encoded file for uploading finished')

    def rename_data_file(self):
        observation_receiving_decoded_data_path = Path(self.observation_receiving_decoded_data)
        if observation_receiving_decoded_data_path.exists():
            observation_receiving_decoded_data_path.rename(Path(
                self.observation_done_decoded_data))
            LOGGER.info('Rename data file for uploading finished')

    def plot_waterfall(self, waterfall):
        vmin = None
        vmax = None
        if not settings.SATNOGS_WATERFALL_AUTORANGE:
            vmin = settings.SATNOGS_WATERFALL_MIN_VALUE
            vmax = settings.SATNOGS_WATERFALL_MAX_VALUE
        waterfall.plot(self.observation_waterfall_png, vmin, vmax)

    def remove_waterfall_file(self):
        try:
            Path(self.observation_waterfall_file).unlink()
        except FileNotFoundError:
            LOGGER.error('Failed to remove waterfall file')
