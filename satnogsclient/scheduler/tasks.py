import logging
import os
import signal
from dateutil import parser
from urlparse import urljoin
from multiprocessing import Process
from satnogsclient.scheduler import scheduler
import subprocess

import requests

from satnogsclient import settings
from satnogsclient.observer.observer import Observer

logger = logging.getLogger('default')
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
    frequency = 100e6
    if obj['origin'] == 'manual':
        user_args = obj['user_args']
        script_name = obj['script_name']
        if '--rx-freq=' in user_args:
            frequency = int(user_args.split('--rx-freq=')[1].split(' ')[0])
    else:
        user_args = ""
        frequency = obj['frequency']
        script_name = settings.GNURADIO_FM_SCRIPT_FILENAME
        if 'mode' in obj:
            if obj['mode'] == "CW":
                script_name = settings.GNURADIO_CW_SCRIPT_FILENAME
            elif obj['mode'] == "APT":
                script_name = settings.GNURADIO_APT_SCRIPT_FILENAME
            elif obj['mode'].startswith('BPSK'):
                script_name = settings.GNURADIO_BPSK_SCRIPT_FILENAME
            elif obj['mode'].endswith('FSK9k6'):
                script_name = settings.GNURADIO_FSK9K6_SCRIPT_FILENAME
    setup_kwargs = {
        'observation_id': obj['id'],
        'tle': tle,
        'observation_end': end,
        'frequency': frequency,
        'origin': obj['origin'],
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
                f.startswith('receiving_waterfall') or
                f.startswith('receiving_data') or
                os.stat(file_path).st_size == 0):
            continue
        if f.startswith('satnogs'):
            observation = {'payload': open(file_path, 'rb')}
        elif f.startswith('waterfall'):
            observation = {'waterfall': open(file_path, 'rb')}
        elif f.startswith('data'):
            observation = {'demoddata': open(file_path, 'rb')}
        else:
            logger.debug('Ignore file: {0}', f)
            continue
        if '_' not in f:
            continue
        observation_id = f.split('_')[1]
        logger.info(
            'Trying to PUT observation data for id: {0}'.format(observation_id))
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
                                stream=True,
                                timeout=45)
        if response.status_code == 200:
            logger.info('Success: status code 200')
            if settings.SATNOGS_COMPLETE_OUTPUT_PATH != "":
                os.rename(os.path.join(settings.SATNOGS_OUTPUT_PATH, f), os.path.join(settings.SATNOGS_COMPLETE_OUTPUT_PATH, f))
            else:
                os.remove(os.path.join(settings.SATNOGS_OUTPUT_PATH, f))
        else:
            logger.error('Bad status code: {0}'.format(response.status_code))
            os.rename(os.path.join(settings.SATNOGS_OUTPUT_PATH, f), os.path.join(settings.SATNOGS_INCOMPLETE_OUTPUT_PATH, f))


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
        url, params=params, headers=headers,
        verify=settings.SATNOGS_VERIFY_SSL, timeout=45)

    if not response.status_code == 200:
        raise Exception(
            'Status code: {0} on request: {1}'.format(response.status_code, url))

    for job in scheduler.get_jobs():
        if job.name in [spawn_observer.__name__]:
            job.remove()

    tasks = []
    for obj in response.json():
        tasks.append(obj)
        start = parser.parse(obj['start'])
        job_id = str(obj['id'])
        obj['origin'] = 'network'
        kwargs = {'obj': obj}
        logger.info('Adding new job: {0}'.format(job_id))
        logger.debug('Observation obj: {0}'.format(obj))
        scheduler.add_job(spawn_observer,
                          'date',
                          run_date=start,
                          id='observer_{0}'.format(job_id),
                          kwargs=kwargs)
    tasks.reverse()


def success_message_to_frontend():
    logger.debug('Successfuly emit to frontend')


def status_listener():
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
    os.environ['GNURADIO_SCRIPT_PID'] = '0'
    os.environ['SCHEDULER'] = 'ON'


def add_observation(obj):
    start = parser.parse(obj['start'])
    job_id = str(obj['id'])
    obj['origin'] = 'manual'
    kwargs = {'obj': obj}
    logger.info('Adding new job: {0}'.format(job_id))
    logger.debug('Observation obj: {0}'.format(obj))
    obs = scheduler.add_job(spawn_observer,
                            'date',
                            run_date=start,
                            id=format(job_id),
                            kwargs=kwargs)
    return obs


def get_observation_list():
    obs_list = scheduler.get_jobs()
    return obs_list


def get_observation(id):
    obs = scheduler.get_job(id)
    return obs


def exec_rigctld():
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
