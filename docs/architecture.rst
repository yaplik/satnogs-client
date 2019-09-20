SatNOGS client architecture
----------------------------

Overview
~~~~~~~~

**SatNOGS client** is the part of our software stack that:

* Fetches observation jobs from the network.
* Schedules locally when the observation starts/ends.
* Does orbital calculation for the position of the observer and the tracked object (using ``PyEphem``).
* Sends ``rotctl/rigctl`` commands to control **SatNOGS** rotator.
* Spawns processes to run demodulation/decoding software with the signal received as input.
* Posts observation data back to the network.

Modules
~~~~~~~

Following the paradigm of **SatNOGS** being extensively modular, **SatNOGS** client is designed to have
discrete modules with specific functionality.

=============
``scheduler``
=============
* Build using ``apscheduler`` library.
* Stores tasks in ``sqlite``.

^^^^^
Tasks
^^^^^
* ``get_jobs``: Queries **SatNOGS Network API** to get jobs scheduled for the ground station.
* ``spawn_observation``: Initiates an ``Observer`` instance and runs the observation.
* ``post_observation_data``: Gathers output files, parses filename and posts data back to **SatNOGS Network API**.

=====================
``observer.observer``
=====================
Given initial description of the observation (``tle``, ``start``, ``end``)
 * Checks input for sanity.
 * Initializes ``WorkerTrack`` and ``WorkerFreq`` instances that start ``rigctl/rotctl``.
   communication using ``trackstart`` method.
 * Starts/Stops GNU Radio script (``gr-satnogs``), which collects the data.
 * Processes produced data from observation (ogg file, waterfall plotting).

===================
``observer.worker``
===================
* Facilitates as a worker for ``rigctl/rotctl``.
* Is the lowest abstraction level on ``rigctl/rotctl`` communications.
* Tracks object until end of observation is reached.

====================
``observer.orbital``
====================
* Implements orbital calculations using ``PyEphem``.
* Provides ``pinpoint`` method the returns alt/az position of tracked object.

==================
``satnogs-client``
==================
* ``satnogs-client``: A console script which runs the scheduler queue in the background and fetch jobs from the network.
