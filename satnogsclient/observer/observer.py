# -*- coding: utf-8 -*-
import logging
import os

from datetime import datetime
from time import sleep
from subprocess import call
from satnogsclient import settings
from satnogsclient.observer.worker import WorkerFreq, WorkerTrack
from satnogsclient.upsat import gnuradio_handler

logger = logging.getLogger('satnogsclient')


class Observer:

    _observation_id = None
    _tle = None
    _observation_end = None
    _frequency = None

    _location = None
    _gnu_proc = None

    _observation_raw_file = None
    _observation_temp_ogg_file = None
    _observation_ogg_file = None

    _rot_ip = settings.ROT_IP
    _rot_port = settings.ROT_PORT

    _rig_ip = settings.RIG_IP
    _rig_port = settings.RIG_PORT

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
    def observation_temp_ogg_file(self):
        return self._observation_temp_ogg_file

    @observation_temp_ogg_file.setter
    def observation_temp_ogg_file(self, observation_temp_ogg_file):
        self._observation_temp_ogg_file = observation_temp_ogg_file

    @property
    def observation_ogg_file(self):
        return self._observation_ogg_file

    @observation_ogg_file.setter
    def observation_ogg_file(self, observation_ogg_file):
        self._observation_ogg_file = observation_ogg_file

    def setup(self, observation_id, tle, observation_end, frequency):
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

        not_completed_prefix = 'receiving_satnogs'
        completed_prefix = 'satnogs'
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S%z')
        raw_file_extension = 'out'
        encoded_file_extension = 'ogg'
        self.observation_raw_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.OUTPUT_PATH,
            not_completed_prefix,
            self.observation_id,
            timestamp, raw_file_extension)
        self.observation_temp_ogg_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.OUTPUT_PATH,
            not_completed_prefix,
            self.observation_id,
            timestamp,
            encoded_file_extension)
        self.observation_ogg_file = '{0}/{1}_{2}_{3}.{4}'.format(
            settings.OUTPUT_PATH,
            completed_prefix,
            self.observation_id,
            timestamp,
            encoded_file_extension)

        return all([self.observation_id, self.tle,
                    self.observation_end, self.frequency,
                    self.observation_raw_file,
                    self.observation_temp_ogg_file,
                    self.observation_ogg_file])

    def observe(self):
        """Starts threads for rotcrl and rigctl."""
        # start thread for rotctl
        logger.info('Start gnuradio thread.')
        self._gnu_proc = gnuradio_handler.exec_gnuradio(
            self.observation_raw_file,
            self.frequency)
        logger.info('Start rotctrl thread.')
        self.run_rot()

        # start thread for rigctl
        logger.info('Start rigctrl thread.')
        self.run_rig()
        # Polling gnuradio process status
        self.poll_gnu_proc_status()
        if "satnogs_fm_demod.py" in settings.GNURADIO_SCRIPT_FILENAME:
            logger.info('Start encoding to ogg.')
            self.ogg_enc()
            logger.info('Rename encoded file for uploading.')
            self.rename_ogg_file()

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
        logger.debug('Frequency {0}'.format(self.frequency))
        logger.debug('Observation end: {0}'.format(self.observation_end))
        self.tracker_freq.trackobject(self.location, self.tle)
        self.tracker_freq.trackstart(5006, False)

    def poll_gnu_proc_status(self):
        while self._gnu_proc.poll() is None:
            sleep(30)
        logger.info('Observation Finished')

    def remove_raw_file(self):
        if os.path.isfile(self.observation_raw_file):
            os.remove(self.observation_raw_file)

    def ogg_enc(self):
        if os.path.isfile(self.observation_raw_file):
            encoded = call(["oggenc", "-r",
                            "--raw-endianness", "0",
                            "-R", "44100", "-B", "16", "-C", "1",
                            "-q", "10", "-o",
                            self.observation_temp_ogg_file,
                            self.observation_raw_file])
            logger.info('Encoding Finished')
            if encoded == 0 and settings.REMOVE_RAW_FILES:
                self.remove_raw_file()

    def rename_ogg_file(self):
        if os.path.isfile(self.observation_temp_ogg_file):
            os.rename(self.observation_temp_ogg_file,
                      self.observation_ogg_file)
        logger.info('Rename encoded file for uploading finished')
