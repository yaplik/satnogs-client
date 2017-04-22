from satnogsclient.web.weblogger import WebLogger
import logging
import os
import signal
import time
import sys
import cPickle
from dateutil import parser
from urlparse import urljoin
from multiprocessing import Process
import json
from satnogsclient.scheduler import scheduler
from flask_socketio import SocketIO
from satnogsclient.upsat.large_data_service import downlink
from satnogsclient.upsat.wod import wod_decode
import subprocess

import requests

from satnogsclient import settings
from satnogsclient.observer.observer import Observer
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.udpsocket import Udpsocket
from satnogsclient.upsat import serial_handler, ecss_logic_utils
from satnogsclient.upsat.gnuradio_handler import read_from_gnuradio
from time import sleep

logging.setLoggerClass(WebLogger)
logger = logging.getLogger('default')
assert isinstance(logger, WebLogger)
socketio = SocketIO(message_queue='redis://')
log_path = settings.SATNOGS_OUTPUT_PATH + "/files/"


def signal_term_handler(a, b):
    p = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if 'satnogs-client' in line:
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
        'lon': settings.SATNOGS_STATION_LON,
        'lat': settings.SATNOGS_STATION_LAT,
        'elev': settings.SATNOGS_STATION_ELEV
    }
    frequency = ""
    if 'user_args' in obj:
        user_args = obj['user_args']
        script_name = obj['script_name']
        if '--rx-freq=' in user_args:
            frequency = int(user_args.split('--rx-freq=')[1].split(' ')[0])
        else:
            frequency = 100e6
    else:
        user_args = ""
        frequency = obj['frequency']
    script_name = settings.GNURADIO_FM_SCRIPT_FILENAME
    if 'mode' in obj:
        if obj['mode'] == "CW":
            script_name = settings.GNURADIO_CW_SCRIPT_FILENAME
    setup_kwargs = {
        'observation_id': obj['id'],
        'tle': tle,
        'observation_end': end,
        'frequency': frequency,
        'user_args': user_args,
        'script_name': script_name
    }

    logger.debug('Observer args: {0}'.format(setup_kwargs))
    setup = observer.setup(**setup_kwargs)

    if setup:
        logger.info('Spawning observer worker.')
        observer.observe()
    else:
        raise RuntimeError('Error in observer setup.')


def post_data():
    logger.info('Post data started')
    """PUT observation data back to Network API."""
    base_url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'data/')
    headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}

    for f in os.walk(settings.SATNOGS_OUTPUT_PATH).next()[2]:
        file_path = os.path.join(*[settings.SATNOGS_OUTPUT_PATH, f])
        if (f.startswith('receiving_satnogs') or
                os.stat(file_path).st_size == 0):
            continue
        observation_id = f.split('_')[1]
        logger.info(
            'Trying to PUT observation data for id: {0}'.format(observation_id))
        if f.startswith('satnogs'):
            observation = {'payload': open(file_path, 'rb')}
        elif f.startswith('waterfall'):
            observation = {'waterfall': open(file_path, 'rb')}
        else:
            logger.debug('Ignore file: {0}', f)
            continue
        url = urljoin(base_url, observation_id)
        if not url.endswith('/'):
            url += '/'
        logger.debug('PUT file {0} to network API'.format(f))
        logger.debug('URL: {0}'.format(url))
        logger.debug('Headers: {0}'.format(headers))
        logger.debug('Observation file: {0}'.format(observation))
        response = requests.put(url, headers=headers,
                                files=observation,
                                verify=settings.SATNOGS_VERIFY_SSL,
                                stream=True)
        if response.status_code == 200:
            logger.info('Success: status code 200')
            dst = os.path.join(settings.SATNOGS_COMPLETE_OUTPUT_PATH, f)
        else:
            logger.error('Bad status code: {0}'.format(response.status_code))
            dst = os.path.join(settings.SATNOGS_INCOMPLETE_OUTPUT_PATH, f)
        os.rename(os.path.join(settings.SATNOGS_OUTPUT_PATH, f), dst)


def get_jobs():
    logger.info('Get jobs started')
    """Query SatNOGS Network API to GET jobs."""
    url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'jobs/')
    params = {'ground_station': settings.SATNOGS_STATION_ID}
    headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}
    logger.debug('URL: {0}'.format(url))
    logger.debug('Params: {0}'.format(params))
    logger.debug('Headers: {0}'.format(headers))
    logger.info('Trying to GET observation jobs from the network')
    response = requests.get(
        url, params=params, headers=headers, verify=settings.SATNOGS_VERIFY_SSL)

    if not response.status_code == 200:
        raise Exception(
            'Status code: {0} on request: {1}'.format(response.status_code, url))

    for job in scheduler.get_jobs():
        if job.name in [spawn_observer.__name__]:
            job.remove()

    sock = Commsocket('127.0.0.1', settings.TASK_FEEDER_TCP_PORT)

    tasks = []
    for obj in response.json():
        tasks.append(obj)
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
            logger.info(
                'Task feeder is terminated or something bad happened to accept')
            return
        if conn:
            data = conn.recv(sock.tasks_buffer_size)
            # Data must be sent to socket.io here
            socketio.emit(
                'backend_msg', json.loads(data), namespace='/control_rx')
            socketio.emit(
                'update_scheduled', json.loads(data), namespace='/update_status')


def ecss_feeder(port):
    sleep(1)
    logger.info('Started ecss feeder')
    sock = Udpsocket(('127.0.0.1', port))
    while 1:
        try:
            conn = sock.recv()
        except IOError:
            logger.info(
                'Ecss feeder is terminated or something bad happened to accept')
            return
        data = ecss_logic_utils.ecss_logic(cPickle.loads(conn[0]))
        # Data must be sent to socket.io here
        socketio.emit('backend_msg', data, namespace='/control_rx',
                      callback=success_message_to_frontend())


def success_message_to_frontend():
    logger.debug('Successfuly emit to frontend')


def status_listener():
    logger.info('Started upsat status listener')
    logger.info('Starting scheduler...')
    scheduler.start()
    scheduler.remove_all_jobs()
    interval = settings.SATNOGS_NETWORK_API_QUERY_INTERVAL
    scheduler.add_job(get_jobs, 'interval', minutes=interval)
    msg = 'Registering `get_jobs` periodic task ({0} min. interval)'.format(
        interval)
    logger.info(msg)
    interval = settings.SATNOGS_NETWORK_API_POST_INTERVAL
    msg = 'Registering `post_data` periodic task ({0} min. interval)'.format(
        interval)
    logger.info(msg)
    scheduler.add_job(post_data, 'interval', minutes=interval)
    tf = Process(target=task_feeder, args=(settings.TASK_FEEDER_TCP_PORT,))
    tf.start()
    d = Process(target=downlink, args=())
    d.daemon = True
    d.start()
    os.environ['TASK_FEEDER_PID'] = str(tf.pid)
    sock = Udpsocket(('127.0.0.1', settings.STATUS_LISTENER_PORT))
    os.environ['BACKEND_TX_PID'] = '0'
    os.environ['BACKEND_RX_PID'] = '0'
    os.environ['BACKEND'] = ""
    os.environ['MODE'] = "network"
    os.environ['ECSS_FEEDER_PID'] = '0'
    os.environ['GNURADIO_SCRIPT_PID'] = '0'
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
                logger.info('Clearing scheduled observations')
                kill_netw_proc()
                os.environ['MODE'] = 'cmd_ctrl'
                ef = Process(
                    target=ecss_feeder, args=(settings.ECSS_FEEDER_UDP_PORT,))
                start_wod_thread()
                ef.start()
                os.environ['ECSS_FEEDER_PID'] = str(ef.pid)
                logger.info('Started ecss_feeder process %d', ef.pid)
            elif dictionary['mode'] == 'network':
                os.environ['MODE'] = 'network'
                kill_cmd_ctrl_proc()
                kill_wod_thread()
                if int(os.environ['ECSS_FEEDER_PID']) != 0:
                    os.kill(int(os.environ['ECSS_FEEDER_PID']), signal.SIGTERM)
                    os.environ['ECSS_FEEDER_PID'] = '0'
                scheduler.remove_all_jobs()
                interval = settings.SATNOGS_NETWORK_API_QUERY_INTERVAL
                scheduler.add_job(get_jobs, 'interval', minutes=interval)
                msg = 'Registering `get_jobs` periodic task ({0} min. interval)'.format(
                    interval)
                logger.info(msg)
                interval = settings.SATNOGS_NETWORK_API_POST_INTERVAL
                msg = 'Registering `post_data` periodic task ({0} min. interval)'.format(
                    interval)
                logger.info(msg)
                scheduler.add_job(post_data, 'interval', minutes=interval)
                tf = Process(
                    target=task_feeder, args=(settings.TASK_FEEDER_TCP_PORT,))
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
    scheduler.remove_all_jobs()
    logger.info('Scheduler shutting down')


def start_wod_thread():
    wd = Process(target=wod_listener, args=())
    wd.daemon = True
    wd.start()
    os.environ['WOD_THREAD_PID'] = str(wd.pid)
    logger.info('WOD listener thread initialized')


def wod_listener():
    sock = Udpsocket(('127.0.0.1', settings.WOD_UDP_PORT))
    while 1:
        try:
            conn, addr = sock.recv()
        except IOError:
            logger.error(
                'WOD listerner is terminated or something bad happened to accept')
            return
        logger.debug("WOD received %s", conn)

        # Write to disk the binary packet
        timestr = time.strftime("%Y%m%d-%H%M%S")
        fwname = log_path + "WOD_RX/wod_" + timestr + ".hex"
        myfile = open(fwname, 'w')
        myfile.write(conn)
        myfile.close()

        data = wod_decode(conn)

        # Write to disk the decoded packet
        timestr = time.strftime("%Y%m%d-%H%M%S")
        fwname = log_path + "WOD_RX_DEC/wod_" + timestr + ".json"
        myfile = open(fwname, 'w')
        myfile.write(str(data['content']))
        myfile.close()

        # Data must be sent to socket.io here
        socketio.emit('backend_msg', data, namespace='/control_rx',
                      callback=success_message_to_frontend())


def kill_wod_thread():
    if 'WOD_THREAD_PID' in os.environ:
        os.kill(int(os.environ['WOD_THREAD_PID']), signal.SIGKILL)
        os.environ['WOD_THREAD_PID'] = '0'


def add_observation(obj):
    start = parser.parse(obj['start'])
    job_id = str(obj['id'])
    kwargs = {'obj': obj}
    logger.info('Adding new job: {0}'.format(job_id))
    logger.debug('Observation obj: {0}'.format(obj))
    obs = scheduler.add_job(spawn_observer,
                            'date',
                            run_date=start,
                            id=format(job_id),
                            kwargs=kwargs)
    socketio.emit('update_scheduled', obj, namespace='/update_status')
    return obs


def get_observation_list():
    obs_list = scheduler.get_jobs()
    return obs_list


def get_observation(id):
    obs = scheduler.get_job(id)
    return obs


def exec_rigctld():
    from multiprocessing import Process
    rig = Process(target=rigctld_subprocess, args=())
    rig.start()


def rigctld_subprocess():
    # Start rigctl daemon
    rig_args = " "
    if settings.RIG_MODEL != "":
        rig_args += "-m " + settings.RIG_MODEL + " "
    if settings.RIG_FILE != "":
        rig_args += "-r " + settings.RIG_FILE + " "
    if settings.RIG_PTT_FILE != "":
        rig_args += "-p " + settings.RIG_PTT_FILE + " "
    if settings.RIG_PTT_TYPE != "":
        rig_args += "-P " + settings.RIG_PTT_TYPE + " "
    if settings.RIG_SERIAL_SPEED != "":
        rig_args += "-s " + settings.RIG_SERIAL_SPEED + " "
    rig_args += "-t " + str(settings.SATNOGS_RIG_PORT)
    logger.info('Starting rigctl daemon')
    os.system("rigctld" + rig_args)
