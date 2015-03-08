# -*- coding: utf-8 -*-
from satnogsclient import settings
from satnogsclient.observer.worker import WorkerFreq, WorkerTrack


class Observer:

    _location = None
    _tle = None
    _observation_end = None
    _frequency = None

    _rot_ip = settings.ROT_IP
    _rot_port = settings.ROT_PORT

    _rig_ip = settings.RIG_IP
    _rig_port = settings.RIG_PORT

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def tle(self):
        return self._tle

    @tle.setter
    def tle(self, tle):
        self._tle = tle

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

    def setup(self, tle, observation_end, frequency):
        """
        Sets up required internal variables.
        returns True if setup is ok
        returns False if setup had problems
        """

        # Set attributes
        self.tle = tle
        self.observation_end = observation_end
        self.frequency = frequency

        return all([self.tle, self.observation_end, self.frequency])

    def observe(self):
        """Starts threads for rotcrl and rigctl."""

        # start thread for rotctl
        self.run_rot()

        # start thread for rigctl
        self.run_rig()

    def run_rot(self):
        self.tracker_rot = WorkerTrack(ip=self.rot_ip,
                                       port=self.rot_port,
                                       time_to_stop=self.observation_end)
        self.tracker_rot.trackobject(self.location, self.tle)
        self.tracker_rot.trackstart()

    def run_rig(self):
        self.tracker_freq = WorkerFreq(ip=self.rig_ip,
                                       port=self.rig_port,
                                       frequency=self.frequency,
                                       time_to_stop=self.observation_end)
        self.tracker_freq.trackobject(self.location, self.tle)
        self.tracker_freq.trackstart()
