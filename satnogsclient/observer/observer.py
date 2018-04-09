import logging
import os

from datetime import datetime
from time import sleep
from subprocess import call
from satnogsclient import settings
from satnogsclient.observer.worker import WorkerFreq, WorkerTrack
from satnogsclient.upsat import gnuradio_handler

logger = logging.getLogger('default')


class Observer(object):

    _gnu_proc = None

    _post_exec_script = settings.SATNOGS_POST_OBSERVATION_SCRIPT
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
        self.observation_end = None
        self.frequency = None
        self.observation_raw_file = None
        self.observation_ogg_file = None
        self.observation_waterfall_file = None
        self.observation_waterfall_png = None
        self.observation_receiving_decoded_data = None
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
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S%z')
        raw_file_extension = 'out'
        encoded_file_extension = 'ogg'
        waterfall_file_extension = 'dat'
        self.observation_raw_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            not_completed_prefix,
            self.observation_id,
            timestamp, raw_file_extension)
        self.observation_ogg_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            completed_prefix,
            self.observation_id,
            timestamp,
            encoded_file_extension)
        self.observation_waterfall_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            receiving_waterfall_prefix,
            self.observation_id,
            timestamp,
            waterfall_file_extension)
        self.observation_waterfall_png = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            waterfall_prefix,
            self.observation_id,
            timestamp,
            'png')
        self.observation_receiving_decoded_data = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            receiving_decoded_data_prefix,
            self.observation_id,
            timestamp,
            'png')
        self.observation_done_decoded_data = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            decoded_data_prefix,
            self.observation_id,
            timestamp,
            'png')
        self.observation_decoded_data = '{0}/{1}_{2}'.format(
            settings.SATNOGS_OUTPUT_PATH,
            decoded_data_prefix,
            self.observation_id)
        return all([self.observation_id, self.tle,
                    self.observation_end, self.frequency,
                    self.observation_raw_file,
                    self.observation_ogg_file,
                    self.observation_waterfall_file,
                    self.observation_waterfall_png,
                    self.observation_decoded_data])

    def observe(self):
        """Starts threads for rotcrl and rigctl."""
        if settings.SATNOGS_PRE_OBSERVATION_SCRIPT is not None:
            logger.info('Executing pre-observation script.')
            os.system(settings.SATNOGS_PRE_OBSERVATION_SCRIPT)

        # if it is APT we want to save with a prefix until the observation
        # is complete, then rename.
        if settings.GNURADIO_APT_SCRIPT_FILENAME in self.script_name:
            self.observation_decoded_data =\
                 self.observation_receiving_decoded_data

        # start thread for rotctl
        logger.info('Start gnuradio thread.')
        self._gnu_proc = gnuradio_handler.exec_gnuradio(
            self.observation_raw_file,
            self.observation_waterfall_file,
            self.frequency,
            self.baud,
            self.script_name,
            self.observation_decoded_data)
        logger.info('Start rotctrl thread.')
        self.run_rot()
        # start thread for rigctl
        logger.info('Start rigctrl thread.')
        self.run_rig()
        # Polling gnuradio process status
        self.poll_gnu_proc_status()
        if "satnogs_generic_iq_receiver.py" not in settings.GNURADIO_SCRIPT_FILENAME:
            logger.info('Rename encoded files for uploading.')
            self.rename_ogg_file()
            self.rename_data_file()
            logger.info('Creating waterfall plot.')
            self.plot_waterfall()

    def run_rot(self):
        self.tracker_rot = WorkerTrack(ip=self.rot_ip,
                                       port=self.rot_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end,
                                       proc=self._gnu_proc,
                                       sleep_time=3)
        logger.debug('TLE: %s', self.tle)
        logger.debug('Observation end: %s', self.observation_end)
        self.tracker_rot.trackobject(self.location, self.tle)
        self.tracker_rot.trackstart()

    def run_rig(self):
        self.tracker_freq = WorkerFreq(ip=self.rig_ip,
                                       port=self.rig_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end,
                                       proc=self._gnu_proc)
        logger.debug('Rig Frequency %s', self.frequency)
        logger.debug('Observation end: %s', self.observation_end)
        self.tracker_freq.trackobject(self.location, self.tle)
        self.tracker_freq.trackstart()

    def poll_gnu_proc_status(self):
        while self._gnu_proc.poll() is None:
            sleep(30)
        logger.info('Observation Finished')
        logger.info('Executing post-observation script.')
        if self._post_exec_script is not None:
            os.system(self._post_exec_script)

    def rename_ogg_file(self):
        if os.path.isfile(self.observation_raw_file):
            os.rename(self.observation_raw_file,
                      self.observation_ogg_file)
        logger.info('Rename encoded file for uploading finished')

    def rename_data_file(self):
        if os.path.isfile(self.observation_receiving_decoded_data):
            os.rename(self.observation_receiving_decoded_data,
                      self.observation_done_decoded_data)
        logger.info('Rename data file for uploading finished')

    def plot_waterfall(self):
        if os.path.isfile(self.observation_waterfall_file):
            plot = call("gnuplot -e \"inputfile='%s'\" \
                         -e \"outfile='%s'\" -e \"height=1600\" \
                        /usr/share/satnogs/scripts/satnogs_waterfall.gp" %
                        (self.observation_waterfall_file,
                         self.observation_waterfall_png),
                        shell=True)
            logger.info('Waterfall plot finished')
            if plot == 0 and settings.SATNOGS_REMOVE_RAW_FILES:
                self.remove_waterfall_file()
        else:
            logger.error('No waterfall data file found')

    def remove_waterfall_file(self):
        if os.path.isfile(self.observation_waterfall_file):
            os.remove(self.observation_waterfall_file)
