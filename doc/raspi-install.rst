======================================
Installing SatNOGS on a Raspberry Pi 3
======================================

This tutorial assumes the following:

1. You have a Raspberry Pi 3 with external power (5V, 2A).

2. USB keyboard, HDMI screen, HDMI cable, network cable (Wi-Fi isn't working on Fedora for now) and a Class 10 SDHC card at least 8GB

3. One of the following sdr devices: RTL-SDR or USRP B200.

4. You have an account and a ground station registered on either `network.satnogs.org <https://network.satnogs.org>`_ or `network-dev.satnogs.org <https://network-dev.satnogs.org>`_. This is needed for getting your ground station ID number and your SatNOGS Network API key.

-----------------------
1. Prepare Raspberry Pi
-----------------------

**Step 1.1:** Download fedora minimal or server RPi image (current 25) from `ARM Fedora Project <https://arm.fedoraproject.org/>`_ (server edition provides a nice web interface, admin console, with several stats and SSH access).

**Step 1.2:** Connect SD card to your computer/laptop and prepare it as described at `Fedora Wiki <https://fedoraproject.org/wiki/Raspberry_Pi#Preparing_the_SD_card>`_ (don't forget to `resize the root partition <https://fedoraproject.org/wiki/Raspberry_Pi#Resizing_the_root_partition>`_).

**Step 1.3:** Attach sdcard to your RPi, plug in the HDMI cable, keyboard and ethernet and turn on the HDMI screen. Plug RPi to the power source.

**Step 1.4:** Fedora installation starts, follow the steps that show up in the screen. You'll have to set root password, timezone and create a new user, e.g. satnogs

**Step 1.5:** From now on you are able to access you RPi directly or through SSH. You can also use admin console if you have selected the fedora server version.

**Step 1.6:** Update fedora package to the latest version by running::
    sudo dnf -y update

**Step 1.7:** Install dependencies for gr-satnogs and satnogs-client::

    sudo dnf install -y util-linux-user git gcc redhat-rpm-config python-devel redis vorbis-tools hamlib gnuradio gnuradio-devel cmake swig fftw3-devel gcc-c++ cppunit cppunit-devel doxygen gr-osmosdr libnova libnova-devel gnuplot libvorbis-devel libffi-devel openssl-devel

**Step 1.8:** Enable Redis service in order to run automatically on startup::

    sudo systemctl enable redis.service

---------------------
2. Install gr-satnogs
---------------------

SatNOGS Client uses GNU Radio scripts in order to get observation data from satelites, gr-satnogs provide this functionality.

**Step 2.1:**: Install gr-satnogs by running the next commands::

    git clone https://github.com/satnogs/gr-satnogs.git
    cd gr-satnogs
    mkdir build
    cd build
    cmake -DLIB_SUFFIX=64 -DCMAKE_INSTALL_PREFIX=/usr ..
    make -j4
    sudo make install
    sudo sh -c 'echo /usr/lib64 > /etc/ld.so.conf.d/lib64.conf'
    sudo ldconfig

-------------------------
3. Install satnogs-client
-------------------------

Building from source is outside of the scope of this document, we will use the packaged install for now.

**Step 3.1:** Run the following command to install the packaged version of SatNOGS Client::

   sudo pip install satnogsclient==0.3

---------------------------
4. Configure satnogs-client
---------------------------

SatNOGS Client needs some configuration before running:

**Step 4.1:** Create a .env file and add station's details as they are defined at SatNOGS Network::

    export SATNOGS_API_TOKEN="1234567890qwertyuiopasdfghjklzxcvbnm1234"
    export SATNOGS_STATION_ID="65"
    export SATNOGS_STATION_LAT="40.662"
    export SATNOGS_STATION_LON="23.337"
    export SATNOGS_STATION_ELEV="150"
    export SATNOGS_NETWORK_API_URL="https://network-dev.satnogs.org/api/"

.. _optional_settings:

**Step 4.2:** There are more option you can export in the created .env file. You will probably need to change the default values of the settings bellow:

  |  SATNOGS_RX_DEVICE
  |    Defines the sdr device. It could be 'usrpb200' or 'rtlsdr'.
  |    Default Type: string
  |    Default Value: 'usrpb200'

  |  SATNOGS_PPM_ERROR
  |    Defines PPM error of sdr, check :doc:`finding-ppm` for more details on PPM. 
  |    Default Type: integer
  |    Default Value: 0

**Step 4.3:** Other optional settings:

  |  SATNOGS_APP_PATH
  |    Defines the path where the sqlite database will be created.
  |    Default Type: string
  |    Default Value: '/tmp/.satnogs'
     
  |  SATNOGS_OUTPUT_PATH
  |    Defines the path where the observation data will be saved.
  |    Default Type: string
  |    Default Value: '/tmp/.satnogs/data'

  |  SATNOGS_COMPLETE_OUTPUT_PATH
  |    Defines the path where data will be moved after succesful upload on network.
  |    Default Type: string
  |    Default Value: '/tmp/.satnogs/data/complete'
     
  |  SATNOGS_INCOMPLETE_OUTPUT_PATH
  |    Defines the path where data will be moved after unsuccesful upload on network.
  |    Default Type: string
  |    Default Value: '/tmp/.satnogs/data/incomplete'

  |  SATNOGS_ROT_IP
  |    Defines IP address where rotctld process listens.
  |    Default Type: string
  |    Default Value: '127.0.0.1'
     
  |  SATNOGS_ROT_PORT
  |    Defines port where rotctld process listens.
  |    Default Type: integer
  |    Default Value: 4533

  |  SATNOGS_RIG_IP
  |    Defines IP address where rigctld process listens.
  |    Default Type: string
  |    Default Value: '127.0.0.1'
     
  |  SATNOGS_RIG_PORT
  |    Defines port where rigctld process listens.
  |    Default Type: integer
  |    Default Value: 4532

---------------------
5. Run satnogs-client
---------------------
^^^^^^^^^^^
1. Manually
^^^^^^^^^^^
In order to manually run satnogs-client you need to follow the next steps:

**Step 5.1.1:** Export all the environment variables::

    source .env

**Step 5.1.2:** Start rotctl daemon(note: given example parameters bellow, you may need to change, add or omit some of them)::

    rotctld -m 202 -r /dev/ttyACM0 -s 19200 &

**Step 5.1.3:** Run the SatNOGS Client::

    satnogs-client

**At this point your client should be fully functional! It will check in with the network URL at a 1 minute interval. You should check your ground station page on the website, the station ID will be in a red box until the station checks in, at which time it will turn green.**

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2. Automaticaly with Supervisord
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Supervisord <http://supervisord.org/introduction.html>`_ is one of the ways to automatically run SatNOGS Client. This is very useful especialy after a power failure or reboot of raspberry pi.

In order to setup supervisord we need to follow the next steps:

**Step 5.2.1:** Install supervisord::

    sudo dnf install -y supervisor

**Step 5.2.2:** Configure supervisord for rotctld

Open your favorite editor and add this into /etc/supervisord/conf.d/rotctld.conf::

   [program:rotctld]
   command=/usr/bin/rotctld <rotctld PARAMETERS>
   autostart=true
   autorestart=true
   user=<USERNAME>
   priority=1

Replace <USERNAME> with the username of the user you have created and <rotctld PARAMETERS> with the parameters needed to run rotctl in your case.

**Step 5.2.3:** Configure supervisord for satnogs-client

Add this into /etc/supervisord/conf.d/satnogs.conf::

   [program:satnogs]
   command=/usr/local/bin/satnogs-client
   autostart=true
   autorestart=true
   user=<USERNAME>
   environment=SATNOGS_NETWORK_API_URL="<URL>",SATNOGS_API_TOKEN="<TOKEN>",SATNOGS_STATION_ID="<ID>",SATNOGS_STATION_LAT="<LATITUDE>",SATNOGS_STATION_LON="<LONGITUDE>",SATNOGS_STATION_ELEV="<ELEVATION>"

Replace <USERNAME> with the username of the user you have created.
Replace <...> instances in environment with the values you used in .env file,
you can also add in this list any other of the :ref:`optional settings <optional_settings>`.

**Step 5.2.4:** Reloading supervisord to get the new configuration::

  sudo supervisorctl reload

With that rotctld and satnogs should have started, you can follow the logs in /var/log/supervisord/.

*NOTE:* In case that you want to change something in satnogs environment variables, like url from the dev one to production one, then you will need to run again Step 5.2.4.
