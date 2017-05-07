======================================
Installing SatNOGS on a Raspberry Pi 3
======================================

This tutorial assumes the following:

1. You have a Raspberry Pi 3 with external power (5V, 2A).

2. USB keyboard, HDMI screen, HDMI cable, network cable (Wi-Fi isn't working on Fedora for now) and a Class 10 SDHC card at least 8GB.

3. One of the following sdr devices: RTL-SDR or USRP B200.

4. You have an account and a ground station registered on either `network.satnogs.org <https://network.satnogs.org>`_ or `network-dev.satnogs.org <https://network-dev.satnogs.org>`_. This is needed for getting your ground station ID number and your SatNOGS Network API key.

-----------------------
1. Prepare Raspberry Pi
-----------------------

**Step 1.1:** Download fedora minimal or server RPi image (current 25) from `ARM Fedora Project <https://arm.fedoraproject.org/>`_ (server edition provides a nice web interface, admin console, with several stats and SSH access).

**Step 1.2:** Connect SD card to your computer/laptop and prepare it as described at `Fedora Wiki <https://fedoraproject.org/wiki/Raspberry_Pi#Preparing_the_SD_card>`_ (don't forget to `resize the root partition <https://fedoraproject.org/wiki/Raspberry_Pi#Resizing_the_root_partition>`_).

**Step 1.3:** Attach sdcard to your RPi, plug in the HDMI cable, keyboard and ethernet and turn on the HDMI screen. Plug RPi to the power source.

**Step 1.4:** Fedora installation starts, follow the steps that show up in the screen. You'll have to setup:
  * root password
  * network connection
  * timezone and ntp server, add at least one, `pool.ntp.org` is suggested
  * a new user, e.g. `satnogs`. Don't forget to set administrator flag and add user to `dialout` group (needed for having access to sdr device).

**Step 1.5:** From now on you are able to access you RPi directly or through SSH. You can also use admin console if you have selected the fedora server version.

**Step 1.6:** Update fedora package to the latest version by running::

    sudo dnf -y update

**Step 1.7:** Install dependencies for gr-satnogs and satnogs-client::

    sudo dnf install -y util-linux-user git gcc redhat-rpm-config python-devel redis vorbis-tools hamlib gnuradio gnuradio-devel cmake swig fftw3-devel gcc-c++ cppunit cppunit-devel doxygen gr-osmosdr libnova libnova-devel gnuplot libvorbis-devel libffi-devel openssl-devel libpng-devel

**Step 1.8:** In order to expand the lifetime of the SD Card, edit /etc/fstab file with your favourite editor:
  * Comment out the line of the swap partition
  * Only if you used the "minimal" Fedora installation (not the "server" build), change options of root partition line (/ ext4) from `defaults,noatime` to `defaults,noatime,commit=1800`. This change means that changes on root partition will be written on SD Card every 30min
  * Move /var/log and /var/tmp directories to memory by adding the following two lines::

      tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=20m 0 0
      tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=80m 0 0

**Step 1.9:** Automate creating of redis directory in /var/log path after boot by running::

    sudo sh -c 'echo "#Type Path                Mode UID   GID   Age Argument" > /etc/tmpfiles.d/logdirs.conf'
    sudo sh -c 'echo "d     /var/log/redis      0750 redis redis 1d  -" >> /etc/tmpfiles.d/logdirs.conf'

**Step 1.10:** Enable and start Redis service in order to run automatically on startup::

    sudo systemctl enable redis.service
    sudo systemctl start redis.service

**Step 1.11:** Configure automatic cleanup of old data (while this is an optional step, if old files are not cleaned out regularly you run the risk of filling your disk over time)
  * As-is this will clean out files older than 1 week. Adjust mtime to your liking
  * Create /etc/cron.daily/satnogs with your favorite editor and add the following::

      #!/bin/sh
      find /tmp/.satnogs/data -type f -mtime +7 -delete

  * Then run::

      sudo chmod +x /etc/cron.daily/satnogs

**Step 1.12:** If you used Fedora Server, configure firewall for SatNOGS web user interface
  * Create /usr/lib/firewalld/services/satnogs.xml and add the following::

      <?xml version="1.0" encoding="utf-8"?>
        <service>
        <short>SatNOGS (HTTP)</short>
        <description>HTTP is the protocol used to serve Web pages. If you plan to make your Web server publicly available, enable this option. This option is not required for viewing pages locally or developing Web pages.</description>
        <port protocol="tcp" port="5000"/>
      </service>

  * Then run::

      sudo firewall-cmd --zone=FedoraServer --add-service=satnogs --permanent
      sudo firewall-cmd --zone=FedoraServer --add-service=satnogs

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

**Step 4.1:** Create a .env file in your home directory (`~/.env`) and add station's details as they are defined at SatNOGS Network::

    export SATNOGS_API_TOKEN="1234567890qwertyuiopasdfghjklzxcvbnm1234"
    export SATNOGS_STATION_ID="65"
    export SATNOGS_STATION_LAT="40.662"
    export SATNOGS_STATION_LON="23.337"
    export SATNOGS_STATION_ELEV="150"
    export SATNOGS_NETWORK_API_URL="https://network-dev.satnogs.org/api/"

.. _optional_settings:

**Step 4.2:** There are more option you can export in the created .env file. You will probably need to change the default values of the settings bellow:

SATNOGS_RX_DEVICE
  * Defines the sdr device. It could be 'usrpb200' or 'rtlsdr'.
  * Default Type: string
  * Default Value: 'rtlsdr'

SATNOGS_PPM_ERROR
  * Defines PPM error of sdr, check :doc:`finding-ppm` for more details on PPM.
  * Default Type: integer
  * Default Value: 0

**Step 4.3:** Other optional settings:

SATNOGS_APP_PATH
  * Defines the path where the sqlite database will be created.
  * Default Type: string
  * Default Value: '/tmp/.satnogs'

SATNOGS_OUTPUT_PATH
  * Defines the path where the observation data will be saved.
  * Default Type: string
  * Default Value: '/tmp/.satnogs/data'

SATNOGS_COMPLETE_OUTPUT_PATH
  * Defines the path where data will be moved after succesful upload on network.
  * Default Type: string
  * Default Value: '/tmp/.satnogs/data/complete'

SATNOGS_INCOMPLETE_OUTPUT_PATH
  * Defines the path where data will be moved after unsuccesful upload on network.
  * Default Type: string
  * Default Value: '/tmp/.satnogs/data/incomplete'

SATNOGS_ROT_IP
  * Defines IP address where rotctld process listens.
  * Default Type: string
  * Default Value: '127.0.0.1'

SATNOGS_ROT_PORT
  * Defines port where rotctld process listens.
  * Default Type: integer
  * Default Value: 4533

SATNOGS_RIG_IP
  * Defines IP address where rigctld process listens.
  * Default Type: string
  * Default Value: '127.0.0.1'

SATNOGS_RIG_PORT
  * Defines port where rigctld process listens.
  * Default Type: integer
  * Default Value: 4532

---------------------
5. Prepare SDR Device
---------------------
In order to have access and use SDR device you need to follow the next steps for you device:

^^^^^^^^^^^^
1. USRP B200
^^^^^^^^^^^^
**Step 5.1.1:** Install uhd package::

    sudo dnf install -y uhd

**Step 5.1.2:** Download uhd images::

    sudo /usr/bin/uhd_images_downloader

**Step 5.1.3:** As the access will be only by ssh and not by direct login we are not be able to access SDR device through `Access Control List(ACL) <https://en.wikipedia.org/wiki/Access_control_list>`_, so we need to setup the appropriate udev rules by following the next steps:

  * Copy udev rules from `/usr/lib/udev/rules.d/10-usrp-uhd.rules` to `/etc/udev/rules.d/10-usrp-uhd.rules`::

      sudo cp /usr/lib/udev/rules.d/10-usrp-uhd.rules /etc/udev/rules.d/10-usrp-uhd.rules

  * Replace ACL reference::

      sudo sed -i 's/0", ENV{ID_SOFTWARE_RADIO}="1"/6"/g' /etc/udev/rules.d/10-usrp-uhd.rules

  * Reload udev rules::

      sudo udevadm control --reload-rules

  * Confirm access on device by running (without sudo, just as single user)::

      uhd_find_devices

  * In case you don't have access, make sure that the device is connected and that the created user is member of the `dialout` group by running::

      groups

  * If user isn't member of `dialout` group run (replace satnogs with the username of your user)::

      sudo usermod -aG dialout satnogs

^^^^^^^^^^^^
2. RTL-SDR
^^^^^^^^^^^^
**Step 5.2.1:** As the access will be only by ssh and not by direct login we are not be able to access SDR device through `Access Control List(ACL) <https://en.wikipedia.org/wiki/Access_control_list>`_, so we need to setup the appropriate udev rules by following the next steps:

  * Copy udev rules from `/usr/lib/udev/rules.d/10-rtl-sdr.rules` to `/etc/udev/rules.d/10-rtl-sdr.rules`::

      sudo cp /usr/lib/udev/rules.d/10-rtl-sdr.rules /etc/udev/rules.d/10-rtl-sdr.rules

  * Replace ACL reference and change group ownership::

      sudo sed -i 's/0", ENV{ID_SOFTWARE_RADIO}="1"/6"/g' /etc/udev/rules.d/10-rtl-sdr.rules
      sudo sed -i 's/rtlsdr/dialout/g' /etc/udev/rules.d/10-rtl-sdr.rules

  * Reload udev rules::

      sudo udevadm control --reload-rules

  * If your rtlsdr device was already plugged in, you will need to unplug it and plug it back in. Otherwise, it is safe to plug it in now.

  * In case you don't have access, make sure that the device is connected and that the created user is member of the `dialout` group by running::

      groups

  * If user isn't member of `dialout` group run (replace satnogs with the username of your user)::

      sudo usermod -aG dialout satnogs

  * If you had to take that step, log out and log back in

---------------------
6. Run satnogs-client
---------------------
^^^^^^^^^^^
1. Manually
^^^^^^^^^^^
In order to manually run satnogs-client you need to follow the next steps:

**Step 6.1.1:** Export all the environment variables::

    source .env

**Step 6.1.2:** Start rotctl daemon(note: given example parameters bellow, you may need to change, add or omit some of them. For a Yaesu G-5500 use -m 601 and -s 9600)::

    rotctld -m 202 -r /dev/ttyACM0 -s 19200 &

**Step 6.1.3:** Run the SatNOGS Client::

    satnogs-client

**At this point your client should be fully functional! It will check in with the network URL at a 1 minute interval. You should check your ground station page on the website, the station ID will be in a red box until the station checks in, at which time it will turn green. There are many ways to automate the running and control of satnogs, we will give you 2 options below, supervisord and systemd.**

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2. Automaticaly with Supervisord
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Supervisord <http://supervisord.org/introduction.html>`_ is one of the ways to automatically run SatNOGS Client. This is very useful especialy after a power failure or reboot of raspberry pi.

In order to setup supervisord we need to follow the next steps:

**Step 6.2.1:** Install supervisord::

    sudo dnf install -y supervisor

**Step 6.2.2:** Automate creating of supervisor directory in /var/log path after boot by running::

    sudo sh -c 'echo "d     /var/log/supervisor 0750 root  root  3d  -" >> /etc/tmpfiles.d/logdirs.conf'

**Step 6.2.3:** Configure supervisord for rotctld

Open with sudo and your favorite editor and add this into /etc/supervisord.d/rotctld.ini::

   [program:rotctld]
   command=/usr/bin/rotctld <rotctld PARAMETERS>
   autostart=true
   autorestart=true
   user=<USERNAME>
   priority=1
   stdout_logfile=/var/log/supervisor/rotctld.log
   stderr_logfile=/var/log/supervisor/rotctld-error.log

Replace <USERNAME> with the username of the user you have created and <rotctld PARAMETERS> with the parameters needed to run rotctl in your case.

**Step 6.2.4:** Configure supervisord for satnogs-client

Add this into /etc/supervisord.d/satnogs.ini::

   [program:satnogs]
   command=/usr/bin/satnogs-client
   autostart=true
   autorestart=true
   user=<USERNAME>
   environment=SATNOGS_NETWORK_API_URL="<URL>",SATNOGS_API_TOKEN="<TOKEN>",SATNOGS_STATION_ID="<ID>",SATNOGS_STATION_LAT="<LATITUDE>",SATNOGS_STATION_LON="<LONGITUDE>",SATNOGS_STATION_ELEV="<ELEVATION>"
   stdout_logfile=/var/log/supervisor/satnogs.log
   stderr_logfile=/var/log/supervisor/satnogs-error.log

Replace <USERNAME> with the username of the user you have created.
Replace <...> instances in environment with the values you used in .env file,
you can also add in this list any other of the :ref:`optional settings <optional_settings>`.

**Step 6.2.5:** Reloading supervisord to get the new configuration::

  sudo systemctl enable supervisord.service
  sudo systemctl start supervisord.service

With that rotctld and satnogs-client should have started, you can follow the logs in /var/log/supervisor/.

*NOTE:* In case that you want to change something in .ini files like satnogs environment variables (url from the dev one to production one), then you will need to run::

 sudo supervisorctl reload

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
3. Automaticaly with Systemd
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Systemd <https://www.freedesktop.org/wiki/Software/systemd/>`_ is one of the ways to automatically run SatNOGS Client. This is very useful especialy after a power failure or reboot of raspberry pi.

In order to setup systemd we need to follow the next steps:

**Step 6.3.1:** Create the script which will initialize and run rotctld and satnogs-client in your home directory (`~/start-satnogs-client.sh`) with the following content::

    rotctld <rotctld PARAMETERS> &
    date >> satnogs-auto.log
    source .env
    satnogs-client

Replace <rotctld PARAMETERS> with the parameters needed to run rotctl in your case.

**Step 6.3.2:** Create as root the file /lib/systemd/system/satnogs-client.service and add the following content::

    [Unit]
    Description=Satnogs Client
    Requires=redis.service
    After=redis.service

    [Service]
    User=<USERNAME>
    WorkingDirectory=/home/<USERNAME>/
    ExecStart=/bin/bash start-satnogs-client.sh
    KillMode=control-group

    [Install]
    WantedBy=multi-user.target

Replace <USERNAME> with the username of the user you have created.

**Step 6.3.3:** Enable and start satnogs-client.service::

    sudo systemctl enable satnogs-client.service
    sudo systemctl start satnogs-client.service

With that rotctld and satnogs-client should have started, you can follow the logs with journactl::

    journalctl -u satnogs-client.service

Use `-f` flag if you want to see the latest updates on logs::

    journalctl -f -u satnogs-client.service

*NOTE:* In case that you want to change something in start-satnogs-client.sh, make the change and then run::

    sudo systemctl stop satnogs-client.service
    sudo systemctl start satnogs-client.service

*NOTE:* In case that you want to change something in satnogs-client.service, make the change and then run::

    sudo systemctl daemon-reload
