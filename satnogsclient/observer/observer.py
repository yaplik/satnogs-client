# -*- coding: utf-8 -*-
from satnogsclient.web.weblogger import WebLogger
import logging
import os

from datetime import datetime
from time import sleep
from subprocess import call
from flask_socketio import SocketIO
from satnogsclient import settings
from satnogsclient.observer.worker import WorkerFreq, WorkerTrack
from satnogsclient.upsat import gnuradio_handler

logging.setLoggerClass(WebLogger)
logger = logging.getLogger('default')
assert isinstance(logger, WebLogger)
socketio = SocketIO(message_queue='redis://')


class Observer:

    _observation_id = None
    _tle = None
    _observation_end = None
    _frequency = None

    _location = None
    _gnu_proc = None

    _observation_raw_file = None
    _observation_ogg_file = None
    _observation_waterfall_file = None
    _observation_waterfall_png = None

    _rot_ip = settings.SATNOGS_ROT_IP
    _rot_port = settings.SATNOGS_ROT_PORT

    _rig_ip = settings.SATNOGS_RIG_IP
    _rig_port = settings.SATNOGS_RIG_PORT

    # Variables from settings
    # Mainly present so we can support multiple ground stations from the client

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def rot_ip(self):
        return self._rot_ip

    @rot_ip.setter
    def rot_ip(self, ip):
        self._rot_ip = ip

    @property
    def rot_port(self):
        return self._rot_port

    @rot_port.setter
    def rot_port(self, port):
        self._rot_port = port

    @property
    def rig_ip(self):
        return self._rig_ip

    @rig_ip.setter
    def rig_ip(self, ip):
        self._rig_ip = ip

    @property
    def rig_port(self):
        return self._rig_port

    @rig_port.setter
    def rig_port(self, port):
        self._rig_port = port

    # Passed variables

    @property
    def observation_id(self):
        return self._observation_id

    @observation_id.setter
    def observation_id(self, observation_id):
        self._observation_id = observation_id

    @property
    def tle(self):
        return self._tle

    @tle.setter
    def tle(self, tle):
        self._tle = tle

    @property
    def observation_end(self):
        return self._observation_end

    @observation_end.setter
    def observation_end(self, timestamp):
        self._observation_end = timestamp

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        self._frequency = frequency

    @property
    def observation_raw_file(self):
        return self._observation_raw_file

    @observation_raw_file.setter
    def observation_raw_file(self, observation_raw_file):
        self._observation_raw_file = observation_raw_file

    @property
    def observation_ogg_file(self):
        return self._observation_ogg_file

    @observation_ogg_file.setter
    def observation_ogg_file(self, observation_ogg_file):
        self._observation_ogg_file = observation_ogg_file

    @property
    def observation_waterfall_file(self):
        return self._observation_waterfall_file

    @observation_waterfall_file.setter
    def observation_waterfall_file(self, observation_waterfall_file):
        self._observation_waterfall_file = observation_waterfall_file

    @property
    def observation_waterfall_png(self):
        return self._observation_waterfall_png

    @observation_waterfall_png.setter
    def observation_waterfall_png(self, observation_waterfall_png):
        self._observation_waterfall_png = observation_waterfall_png

    def setup(self, observation_id, tle, observation_end, frequency, user_args, script_name):
        """
        Sets up required internal variables.
        * returns True if setup is ok
        * returns False if issue is encountered
        """

        # Set attributes
        self.observation_id = observation_id
        self.user_args = user_args
        self.script_name = script_name
        self.tle = tle
        self.observation_end = observation_end
        self.frequency = frequency

        not_completed_prefix = 'receiving_satnogs'
        completed_prefix = 'satnogs'
        receiving_waterfall_prefix = 'receiving_waterfall'
        waterfall_prefix = 'waterfall'
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

        return all([self.observation_id, self.tle,
                    self.observation_end, self.frequency,
                    self.observation_raw_file,
                    self.observation_ogg_file,
                    self.observation_waterfall_file,
                    self.observation_waterfall_png])

    def observe(self):
        """Starts threads for rotcrl and rigctl."""
        # start thread for rotctl
        logger.info('Start gnuradio thread.')
        self._gnu_proc = gnuradio_handler.exec_gnuradio(
            self.observation_raw_file,
            self.observation_waterfall_file,
            self.frequency,
            self.user_args,
            self.script_name)
        logger.info('Start rotctrl thread.')
        self.run_rot()
        # start thread for rigctl
        logger.info('Start rigctrl thread.')
        self.run_rig()
        # Polling gnuradio process status
        self.poll_gnu_proc_status()
        if "satnogs_generic_iq_receiver.py" not in settings.GNURADIO_SCRIPT_FILENAME:
            logger.info('Rename encoded file for uploading.')
            self.rename_ogg_file()
            logger.info('Creating waterfall plot.')
            self.plot_waterfall()

    def run_rot(self):
        self.tracker_rot = WorkerTrack(ip=self.rot_ip,
                                       port=self.rot_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end,
                                       proc=self._gnu_proc)
        logger.debug('TLE: {0}'.format(self.tle))
        logger.debug('Observation end: {0}'.format(self.observation_end))
        self.tracker_rot.trackobject(self.location, self.tle)
        self.tracker_rot.trackstart(settings.CURRENT_PASS_TCP_PORT, True)

    def run_rig(self):
        self.tracker_freq = WorkerFreq(ip=self.rig_ip,
                                       port=self.rig_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end,
                                       proc=self._gnu_proc)
        logger.debug('Rig Frequency {0}'.format(self.frequency))
        logger.debug('Observation end: {0}'.format(self.observation_end))
        self.tracker_freq.trackobject(self.location, self.tle)
        self.tracker_freq.trackstart(5006, False)

    def poll_gnu_proc_status(self):
        while self._gnu_proc.poll() is None:
            sleep(30)
        logger.info('Observation Finished')

    def rename_ogg_file(self):
        if os.path.isfile(self.observation_raw_file):
            os.rename(self.observation_raw_file,
                      self.observation_ogg_file)
        logger.info('Rename encoded file for uploading finished')

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
