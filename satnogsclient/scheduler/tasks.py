# -*- coding: utf-8 -*-
import logging
import os
import signal
import time
import sys
import cPickle
from datetime import datetime, timedelta
from dateutil import parser
from urlparse import urljoin
from multiprocessing import Process
import json
from satnogsclient.scheduler import scheduler
from flask_socketio import SocketIO
import subprocess

import pytz
import requests

from satnogsclient import settings
from satnogsclient.observer.observer import Observer
from satnogsclient.receiver import SignalReceiver
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import serial_handler, ecss_logic_utils
from satnogsclient.upsat.gnuradio_handler import read_from_gnuradio
from time import sleep

logger = logging.getLogger('satnogsclient')
socketio = SocketIO(message_queue='redis://')


def signal_term_handler(a, b):
    p = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if 'satnogs-poller' in line:
            pid = int(line.split(None, 2)[1])
            os.kill(pid, signal.SIGKILL)


signal.signal(signal.SIGINT, signal_term_handler)


def spawn_observer(*args, **kwargs):
    obj = kwargs.pop('obj')
    tle = {
        'tle0': obj['tle0'],
        'tle1': obj['tle1'],
        'tle2': obj['tle2']
    }
    end = parser.parse(obj['end'])

    observer = Observer()
    observer.location = {
        'lon': settings.GROUND_STATION_LON,
        'lat': settings.GROUND_STATION_LAT,
        'elev': settings.GROUND_STATION_ELEV
    }

    setup_kwargs = {
        'observation_id': obj['id'],
        'tle': tle,
        'observation_end': end,
        'frequency': obj['frequency']
    }

    logger.debug('Observer args: {0}'.format(setup_kwargs))
    setup = observer.setup(**setup_kwargs)

    if setup:
        logger.info('Spawning observer worker.')
        observer.observe()
    else:
        raise RuntimeError('Error in observer setup.')


def spawn_receiver(*args, **kwargs):
    obj = kwargs.pop('obj')
    logger.debug('Receiver args: {0}'.format(obj))
    receiver = SignalReceiver(obj['id'], obj['frequency'])
    logger.info('Spawning receiver worker.')
    receiver.run()
    end = parser.parse(obj['end'])

    while True:
        if datetime.now(pytz.utc) < end:
            time.sleep(1)
        else:
            receiver.stop()
            break


def post_data():
    logger.info('Post data started')
    """PUT observation data back to Network API."""
    base_url = urljoin(settings.NETWORK_API_URL, 'data/')
    headers = {'Authorization': 'Token {0}'.format(settings.API_TOKEN)}

    for f in os.walk(settings.OUTPUT_PATH).next()[2]:
        # Ignore files in receiving state
        if f.startswith('receiving'):
            continue
        observation_id = f.split('_')[1]
        logger.info('Trying to PUT observation data for id: {0}'.format(observation_id))
        file_path = os.path.join(*[settings.OUTPUT_PATH, f])
        observation = {'payload': open(file_path, 'rb')}
        url = urljoin(base_url, observation_id)
        if not url.endswith('/'):
            url += '/'
        logger.debug('PUT file {0} to network API'.format(f))
        logger.debug('URL: {0}'.format(url))
        logger.debug('Headers: {0}'.format(headers))
        logger.debug('Observation file: {0}'.format(observation))
        response = requests.put(url, headers=headers,
                                files=observation,
                                verify=settings.VERIFY_SSL)
        if response.status_code == 200:
            logger.info('Success: status code 200')
            dst = os.path.join(settings.COMPLETE_OUTPUT_PATH, f)
        else:
            logger.error('Bad status code: {0}'.format(response.status_code))
            dst = os.path.join(settings.INCOMPLETE_OUTPUT_PATH, f)
        os.rename(os.path.join(settings.OUTPUT_PATH, f), dst)


def get_jobs():
    logger.info('Get jobs started')
    """Query SatNOGS Network API to GET jobs."""
    url = urljoin(settings.NETWORK_API_URL, 'jobs/')
    params = {'ground_station': settings.GROUND_STATION_ID}
    headers = {'Authorization': 'Token {0}'.format(settings.API_TOKEN)}
    logger.debug('URL: {0}'.format(url))
    logger.debug('Params: {0}'.format(params))
    logger.debug('Headers: {0}'.format(headers))
    logger.info('Trying to GET observation jobs from the network')
    response = requests.get(url, params=params, headers=headers, verify=settings.VERIFY_SSL)

    if not response.status_code == 200:
        raise Exception('Status code: {0} on request: {1}'.format(response.status_code, url))

    for job in scheduler.get_jobs():
        if job.name in [spawn_observer.__name__, spawn_receiver.__name__]:
            job.remove()

    sock = Commsocket('127.0.0.1', settings.TASK_FEEDER_TCP_PORT)

    tasks = []
    for obj in response.json():
        tasks.append(obj)
        start = parser.parse(obj['start'])
        job_id = str(obj['id'])
        kwargs = {'obj': obj}
        receiver_start = start - timedelta(seconds=settings.DEMODULATOR_INIT_TIME)
        logger.info('Adding new job: {0}'.format(job_id))
        logger.debug('Observation obj: {0}'.format(obj))
        scheduler.add_job(spawn_observer,
                          'date',
                          run_date=start,
                          id='observer_{0}'.format(job_id),
                          kwargs=kwargs)
        scheduler.add_job(spawn_receiver,
                          'date',
                          run_date=receiver_start,
                          id='receiver_{0}'.format(job_id),
                          kwargs=kwargs)
    tasks.reverse()

    while sys.getsizeof(json.dumps(tasks)) > sock.tasks_buffer_size:
        tasks.pop()

    b = sock.connect()
    if b:
        sock.send_not_recv(json.dumps(tasks))
    else:
        logger.info('Task listener thread not online')


def task_feeder(port):
    sleep(1)
    logger.info('Started task feeder')
    sock = Commsocket('127.0.0.1', port)
    sock.bind()
    sock.listen()
    while 1:
        try:
            conn = sock.accept()
        except IOError:
            logger.info('Task feeder is terminated or something bad happened to accept')
            return
        if conn:
            data = conn.recv(sock.tasks_buffer_size)
            # Data must be sent to socket.io here
            socketio.emit('backend_msg', data, namespace='/control_rx')


def ecss_feeder(port):
    sleep(1)
    logger.info('Started ecss feeder')
    sock = Udpsocket(('127.0.0.1', port))
    while 1:
        try:
            conn = sock.recv()
        except IOError:
            logger.info('Ecss feeder is terminated or something bad happened to accept')
            return
        data = ecss_logic_utils.ecss_logic(cPickle.loads(conn[0]))
        # Data must be sent to socket.io here
        socketio.emit('backend_msg', data, namespace='/control_rx', callback=success_message_to_frontend())


def success_message_to_frontend():
    logger.debug('Successfuly emit to frontend')


def status_listener():
    logger.info('Started upsat status listener')
    logger.info('Starting scheduler...')
    scheduler.start()
    scheduler.remove_all_jobs()
    interval = settings.NETWORK_API_QUERY_INTERVAL
    scheduler.add_job(get_jobs, 'interval', minutes=interval)
    msg = 'Registering `get_jobs` periodic task ({0} min. interval)'.format(interval)
    logger.info(msg)
    interval = settings.NETWORK_API_POST_INTERVAL
    msg = 'Registering `post_data` periodic task ({0} min. interval)'.format(interval)
    logger.info(msg)
    scheduler.add_job(post_data, 'interval', minutes=interval)
    tf = Process(target=task_feeder, args=(settings.TASK_FEEDER_TCP_PORT,))
    tf.start()
    os.environ['TASK_FEEDER_PID'] = str(tf.pid)
    sock = Udpsocket(('127.0.0.1', settings.STATUS_LISTENER_PORT))
    os.environ['BACKEND_TX_PID'] = '0'
    os.environ['BACKEND_RX_PID'] = '0'
    os.environ['BACKEND'] = ""
    os.environ['MODE'] = "network"
    os.environ['ECSS_FEEDER_PID'] = '0'
    os.environ['SCHEDULER'] = 'ON'
    while 1:
        conn = sock.recv()
        dictionary = json.loads(conn[0])
        if 'backend' in dictionary.keys():
            if dictionary['backend'] == os.environ['BACKEND']:
                continue
            kill_cmd_ctrl_proc()
            if dictionary['backend'] == 'gnuradio':
                if os.environ['BACKEND'] == 'serial':
                    serial_handler.close()
                os.environ['BACKEND'] = 'gnuradio'
                rx = Process(target=read_from_gnuradio, args=())
                rx.daemon = True
                rx.start()
                logger.info('Started gnuradio rx process %d', rx.pid)
                os.environ['BACKEND_RX_PID'] = str(rx.pid)
            elif dictionary['backend'] == 'serial':
                os.environ['BACKEND'] = 'serial'
                serial_handler.init()
                rx = Process(target=serial_handler.read_from_serial, args=())
                rx.daemon = True
                rx.start()
                os.environ['BACKEND_RX_PID'] = str(rx.pid)
        if 'mode' in dictionary.keys():
            if dictionary['mode'] == os.environ['MODE']:
                continue
            logger.info('Changing mode')
            if dictionary['mode'] == 'cmd_ctrl':
                logger.info('Starting ecss feeder thread...')
                os.environ['MODE'] = 'cmd_ctrl'
                kill_netw_proc()
                ef = Process(target=ecss_feeder, args=(settings.ECSS_FEEDER_UDP_PORT,))
                ef.start()
                os.environ['ECSS_FEEDER_PID'] = str(ef.pid)
                logger.info('Started ecss_feeder process %d', ef.pid)
            elif dictionary['mode'] == 'network':
                os.environ['MODE'] = 'network'
                kill_cmd_ctrl_proc()
                if int(os.environ['ECSS_FEEDER_PID']) != 0:
                    os.kill(int(os.environ['ECSS_FEEDER_PID']), signal.SIGTERM)
                    os.environ['ECSS_FEEDER_PID'] = '0'
                os.environ['SCHEDULER'] = 'ON'
                scheduler.start()
                tf = Process(target=task_feeder, args=(settings.TASK_FEEDER_TCP_PORT,))
                tf.start()
                os.environ['TASK_FEEDER_PID'] = str(tf.pid)
                logger.info('Started task feeder process %d', tf.pid)


def kill_cmd_ctrl_proc():
    if int(os.environ['BACKEND_RX_PID']) != 0:
        os.kill(int(os.environ['BACKEND_RX_PID']), signal.SIGKILL)
        os.environ['BACKEND_RX_PID'] = '0'


def kill_netw_proc():
    if int(os.environ['TASK_FEEDER_PID']) != 0:
        logger.info('Killing feeder %d', int(os.environ['TASK_FEEDER_PID']))
        os.kill(int(os.environ['TASK_FEEDER_PID']), signal.SIGTERM)
        os.environ['TASK_FEEDER_PID'] = '0'
    scheduler.shutdown()
    logger.info('Scheduler shutting down')


def add_observation(obj):
    start = parser.parse(obj['start'])
    job_id = str(obj['id'])
    kwargs = {'obj': obj}
    logger.info('Adding new job: {0}'.format(job_id))
    logger.debug('Observation obj: {0}'.format(obj))
    scheduler.add_job(spawn_observer,
                        'date',
                        run_date=start,
                        id='observer_{0}'.format(job_id),
                        kwargs=kwargs)
