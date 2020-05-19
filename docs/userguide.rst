User guide
==========

Requirements
------------

- Python 3.6+
- Hamlib 3.3+ Python bindings


Installation
------------

Debian
^^^^^^

To install the required dependencies in Debian run::

  $ apt-get install python3-libhamlib2


SatNOGS Client
^^^^^^^^^^^^^^

To install SatNOGS Client run::

  $ pip install satnogs-client

This will install a console script called ``satnogs-client``.


.. _configuration:

Configuration
-------------

Configuration of SatNOGS Client is done through environment variables.
The environment variables can also be defined in a file called ``.env``, place on the project root directory.
The format of each line in ``.env`` file is ``VARIABLE=VALUE``.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

SATNOGS_API_TOKEN
~~~~~~~~~~~~~~~~~

:Type: *string*
:Default: *None*
:Required: *Yes*
:Description:
   SatNOGS API token associated with an account in SatNOGS Network.
   This token is secret.
   It can be found in SatNOGS Network user page.


SATNOGS_PRE_OBSERVATION_SCRIPT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Type: *path*
:Default: *None*
:Required: *No*
:Description:
   A path to an executable to be executed before an observation job is started.
   Execution of this script blocks the observation job.


SATNOGS_POST_OBSERVATION_SCRIPT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Type: *path*
:Default: *None*
:Required: *No*
:Description:
   A path to an executable to be executed after an observation job has finished.
   Execution of this script blocks the completion of an observation job.


SATNOGS_STATION_ID
~~~~~~~~~~~~~~~~~~

:Type: *integer*
:Default: *None*
:Required: *Yes*
:Description:
   The ID of the SatNOGS Network station this client will act as.
   The station must be owned by the user with the defined API token.


SATNOGS_STATION_LAT
~~~~~~~~~~~~~~~~~~~

:Type: *float*
:Default: *None*
:Required: *Yes*
:Description:
   Latitude of the station location.
   Higher precision of this value increases accuracy of doppler correcton while lower precision increases station location privacy.


SATNOGS_STATION_LON
~~~~~~~~~~~~~~~~~~~

:Type: *float*
:Default: *None*
:Required: *Yes*
:Description:
   Longitude of the station location.
   Higher precision of this value increases accuracy of doppler correcton while lower precision increases station location privacy.


SATNOGS_STATION_ELEV
~~~~~~~~~~~~~~~~~~~~

:Type: *integer*
:Default: *None*
:Required: *Yes*
:Description:
   Elevation of the station location.
   Higher precision of this value increases accuracy of doppler correcton while lower precision increases station location privacy.


SATNOGS_GPSD_CLIENT_ENABLED
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Type: *boolean*
:Default: *False*
:Required: *No*
:Description:
   Enable SatNOGS Client to connect to a GPSd daemon to pull positional information.
   The position is queried once, during SatNOGS Client startup.


SATNOGS_GPSD_HOST
~~~~~~~~~~~~~~~~~

:Type: *host*
:Default: ``127.0.0.1``
:Required: *No*
:Description:
   Hostname or IP address of GPSd to connecct to for pulling positional information.


SATNOGS_GPSD_PORT
~~~~~~~~~~~~~~~~~

:Type: *port*
:Default: ``2947``
:Required: *No*
:Description:
   Port of GPSd to connect to for pulling positional information.


SATNOGS_GPSD_TIMEOUT
~~~~~~~~~~~~~~~~~~~~

:Type: *port*
:Default: ``0``
:Required: *No*
:Description:
   Time to wait until GPSd returns positional information.
   A value of 0 means to wait indefinitely.


SATNOGS_APP_PATH
~~~~~~~~~~~~~~~~

:Type: *path*
:Default: ``/tmp/.satnogs``
:Required: *No*
:Description:
   Base path for storing output files.


SATNOGS_OUTPUT_PATH
~~~~~~~~~~~~~~~~~~~

:Type: *path*
:Default: ``/tmp/.satnogs/data``
:Required: *No*
:Description:
   Path for storing output files.


SATNOGS_COMPLETE_OUTPUT_PATH
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Type: *path*
:Default:
:Required: *No*
:Description:
   Path to move output files once they are completed.
   Preserving output files is disabled if set to empty.


SATNOGS_INCOMPLETE_OUTPUT_PATH
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *path*
:Default: ``/tmp/.satnogs/data/incomplete``
:Required: *No*
:Description:
   Path for moving incomplete output files.


SATNOGS_REMOVE_RAW_FILES
~~~~~~~~~~~~~~~~~~~~~~~~

:Type: *boolean*
:Default: *True*
:Required: *No*
:Description:
   Remove raw data files used for generating waterfalls.


SATNOGS_VERIFY_SSL
~~~~~~~~~~~~~~~~~~

:Type: *boolean*
:Default: *True*
:Required: *No*
:Description:
   Verify SSL certificates for HTTPS requests.


SATNOGS_NETWORK_API_URL
~~~~~~~~~~~~~~~~~~~~~~~

:Type: *url*
:Default: ``https://network.satnogs.org/api/``
:Required: *No*
:Description:
   URL pointing to API of SatNOGS Network.


SATNOGS_NETWORK_API_QUERY_INTERVAL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: ``60``
:Required: *No*
:Description:
   Interval (in seconds) for pulling jobs form SatNOGS Network API.


SATNOGS_NETWORK_API_POST_INTERVAL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: ``180``
:Required: *No*
:Description:
   Interval (in seconds) for posting observation data to SatNOGS Network API.


SATNOGS_ROT_MODEL
~~~~~~~~~~~~~~~~~

:Type: *string*
:Default: ``ROT_MODEL_DUMMY``
:Required: *No*
:Description:
   Rotator model to control.
   This value must be the model string of a Hamlib rotator.


SATNOGS_ROT_BAUD
~~~~~~~~~~~~~~~~

:Type: *integer*
:Default: ``19200``
:Required: *No*
:Description:
   Hamlib rotator serial interface baud rate.


SATNOGS_ROT_PORT
~~~~~~~~~~~~~~~~

:Type: *path*
:Default: ``/dev/ttyUSB0``
:Required: *No*
:Description:
   Path to Hamlib rotator serial port device.
   The device must be accessible to the user which SatNOGS Client is running.


SATNOGS_RIG_IP
~~~~~~~~~~~~~~

:Type: *host*
:Default: ``127.0.0.1``
:Required: *No*
:Description:
   Hostname or IP address of Hamlib rotctld.


SATNOGS_RIG_PORT
~~~~~~~~~~~~~~~~

:Type: *integer*
:Default: ``4532``
:Required: *No*
:Description:
   Hamlib rigctld TCP port.


SATNOGS_ROT_THRESHOLD
~~~~~~~~~~~~~~~~~~~~~

:Type: *integer*
:Default: ``4``
:Required: *No*
:Description:
   Azimuth/elevation threshold for moving the rotator.
   Position changes below this threshold will not cause the rotator to move.


SATNOGS_ROT_FLIP
~~~~~~~~~~~~~~~~

:Type: *boolean*
:Default: *False*
:Required: *No*
:Description:
   Enable rotator flipping during high elevation passes.


SATNOGS_ROT_FLIP_ANGLE
~~~~~~~~~~~~~~~~~~~~~~

:Type: *integer*
:Default: ``75``
:Required: *No*
:Description:
   Elevation angle above which the rotator will flip.


SATNOGS_SOAPY_RX_DEVICE
~~~~~~~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *Yes*
:Description:
   FIXME


SATNOGS_RX_SAMP_RATE
~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: *None*
:Required: *Yes*
:Description:
   FIXME


SATNOGS_RX_BANDWIDTH
~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_DOPPLER_CORR_PER_SEC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_LO_OFFSET
~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_PPM_ERROR
~~~~~~~~~~~~~~~~~
:Type: *float*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_GAIN_MODE
~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: ``Overall``
:Required: *No*
:Description:
   FIXME


SATNOGS_RF_GAIN
~~~~~~~~~~~~~~~
:Type: *float*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_ANTENNA
~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *Yes*
:Description:
   FIXME


SATNOGS_DEV_ARGS
~~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_STREAM_ARGS
~~~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_TUNE_ARGS
~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_OTHER_SETTINGS
~~~~~~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_DC_REMOVAL
~~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *No*
:Description:
   FIXME


SATNOGS_BB_FREQ
~~~~~~~~~~~~~~~
:Type: *string*
:Default: *None*
:Required: *No*
:Description:
   FIXME


ENABLE_IQ_DUMP
~~~~~~~~~~~~~~
:Type: *boolean*
:Default: *False*
:Required: *No*
:Description:
   Create I/Q data dumps for every observation.
   Use this feature with caution.
   Enabling this setting will store large amount of data on the filesystem.


IQ_DUMP_FILENAME
~~~~~~~~~~~~~~~~
:Type: *boolean*
:Default: *False*
:Required: *No*
:Description:
   Path to file for storing I/Q data dumps.


DISABLE_DECODED_DATA
~~~~~~~~~~~~~~~~~~~~
:Type: *boolean*
:Default: *False*
:Required: *No*
:Description:
   Disable output of decoded data.


SATNOGS_WATERFALL_AUTORANGE
~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *boolean*
:Default: *True*
:Required: *No*
:Description:
   Automatically set power level range of waterfall images.


SATNOGS_WATERFALL_MIN_VALUE
~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: ``-100``
:Required: *No*
:Description:
   Minimum power level of waterfall images.


SATNOGS_WATERFALL_MAX_VALUE
~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type: *integer*
:Default: ``-50``
:Required: *No*
:Description:
   Maximum power level of waterfall images.


LOG_LEVEL
~~~~~~~~~
:Type: *string*
:Default: ``WARNING``
:Required: *No*
:Description:
   SatNOGS Client logging level.
   Valid values are:
     * ``CRITICAL``
     * ``ERROR``
     * ``WARNING``
     * ``INFO``
     * ``DEBUG``


SCHEDULER_LOG_LEVEL
~~~~~~~~~~~~~~~~~~~
:Type: *string*
:Default: ``WARNING``
:Required: *No*
:Description:
   SatNOGS Client scheduler logging level.
   Valid values are:
     * ``CRITICAL``
     * ``ERROR``
     * ``WARNING``
     * ``INFO``
     * ``DEBUG``


SENTRY_DSN
~~~~~~~~~~
:Type: *string*
:Default: d50342fb75aa8f3945e2f846b77a0cdb7c7d2275
:Required: *No*
:Description:
   Sentry Data Source Name used for sending events to application monitoring and error tracking server.


SENTRY_ENABLED
~~~~~~~~~~~~~~
:Type: *boolean*
:Default: *False*
:Required: *No*
:Description:
   Enable sending events to Sentry application monitoring and error tracking server.


Usage
-----

To execute the script, run it on the command line::

  $ satnogs-client
