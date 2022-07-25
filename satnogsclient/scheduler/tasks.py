from __future__ import absolute_import, division, print_function

import base64
import json
import logging
import os
import threading
from datetime import datetime, timedelta

import pytz
import requests
from dateutil import parser

from satnogsclient import settings
from satnogsclient.locator import locator
from satnogsclient.observer.observer import Observer
from satnogsclient.scheduler import SCHEDULER

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

LOGGER = logging.getLogger(__name__)
OBSERVER_LOCK = threading.Lock()


def spawn_observer(**kwargs):
    obj = kwargs.pop('obj')
    tle = {'tle0': obj['tle0'], 'tle1': obj['tle1'], 'tle2': obj['tle2']}
    end = parser.parse(obj['end'])

    observer = Observer()
    observer.location = {
        'lon': settings.SATNOGS_STATION_LON,
        'lat': settings.SATNOGS_STATION_LAT,
        'elev': settings.SATNOGS_STATION_ELEV
    }

    # Get the baudrate. In case of CW baudrate equals the WPM
    baud = 0
    if 'baud' in obj:
        baud = obj['baud']

    setup_kwargs = {
        'observation_id': obj['id'],
        'tle': tle,
        'observation_end': end,
        'frequency': obj['frequency'],
        'mode': obj['mode'],
        'baud': baud
    }

    LOGGER.debug('Observer args: %s', setup_kwargs)
    setup = observer.setup(**setup_kwargs)

    if setup:
        LOGGER.info('Spawning observer worker.')
        timeout_timedelta = end - datetime.now(pytz.utc)
        if timeout_timedelta.total_seconds() == 0:
            timeout_timedelta = timedelta()
        if not OBSERVER_LOCK.acquire(timeout=timeout_timedelta.total_seconds()):
            LOGGER.error('Observer job lock acquiring timed out.')
            return
        observer.observe()
        OBSERVER_LOCK.release()
    else:
        raise RuntimeError('Error in observer setup.')


def keep_or_remove_file(filename):
    # If set, move uploaded file to `SATNOGS_COMPLETE_OUTPUT_PATH`,
    # otherwise delete it
    if settings.SATNOGS_COMPLETE_OUTPUT_PATH != '':
        os.rename(os.path.join(settings.SATNOGS_OUTPUT_PATH, filename),
                  os.path.join(settings.SATNOGS_COMPLETE_OUTPUT_PATH, filename))
    else:
        os.remove(os.path.join(settings.SATNOGS_OUTPUT_PATH, filename))


def post_data():
    """PUT observation data back to Network API."""
    LOGGER.info('Post data started')

    for fil in next(os.walk(settings.SATNOGS_OUTPUT_PATH))[2]:
        file_path = os.path.join(*[settings.SATNOGS_OUTPUT_PATH, fil])
        if (fil.startswith('receiving_satnogs') or fil.startswith('receiving_waterfall')
                or fil.startswith('receiving_data') or os.stat(file_path).st_size == 0):
            continue
        if fil.startswith('satnogs'):
            if not settings.SATNOGS_UPLOAD_AUDIO_FILES:
                keep_or_remove_file(fil)
                continue
            observation = {'payload': open(file_path, 'rb')}
        elif fil.startswith('waterfall'):
            if not settings.SATNOGS_UPLOAD_WATERFALL_FILES:
                keep_or_remove_file(fil)
                continue
            observation = {'waterfall': open(file_path, 'rb')}
        elif fil.startswith('data'):
            try:
                with open(file_path, 'r') as json_string:
                    data = json.load(json_string)
                observation = {'demoddata': (fil, base64.b64decode(data['pdu']))}
            except ValueError:
                observation = {'demoddata': open(file_path, 'rb')}
        else:
            LOGGER.debug('Ignore file: %s', fil)
            continue
        if '_' not in fil:
            continue
        observation_id = fil.split('_')[1]
        upload_observation_data(observation_id, observation, fil)


def upload_observation_data(observation_id, observation, fil):
    """Upload observation data to SatNOGS Network API."""
    base_url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'observations/')
    headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}

    LOGGER.info('Trying to PUT observation data for id: %s', observation_id)
    url = urljoin(base_url, observation_id)
    if not url.endswith('/'):
        url += '/'
    LOGGER.debug('PUT file %s to network API', fil)
    LOGGER.debug('URL: %s', url)
    LOGGER.debug('Headers: %s', headers)
    LOGGER.debug('Observation file: %s', observation)
    try:
        response = requests.put(url,
                                headers=headers,
                                files=observation,
                                verify=settings.SATNOGS_VERIFY_SSL,
                                stream=True,
                                timeout=settings.SATNOGS_NETWORK_API_TIMEOUT)
        response.raise_for_status()

        LOGGER.info('Upload successful.')

        keep_or_remove_file(fil)

        import sys
        sys.exit(0)
    except requests.exceptions.Timeout:
        LOGGER.error('Upload of %s for observation %s failed '
                     'due to timeout.', fil, observation_id)
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            LOGGER.error(
                "Upload of %s for observation %s failed, %s doesn't exist (404)."
                'Probably the observation was deleted.', fil, observation_id, url)

            # Move file to `SATNOGS_INCOMPLETE_OUTPUT_PATH`
            os.rename(os.path.join(settings.SATNOGS_OUTPUT_PATH, fil),
                      os.path.join(settings.SATNOGS_INCOMPLETE_OUTPUT_PATH, fil))
        if response.status_code == 403 and 'has already been uploaded' in response.text:
            LOGGER.error('Upload of %s for observation %s is forbidden, %s\n URL: %s', fil,
                         observation_id, response.text, url)
            keep_or_remove_file(fil)
        else:
            LOGGER.error('Upload of %s for observation %s failed, '
                         'response status code: %s', fil, observation_id, response.status_code)


def get_jobs():
    """Query SatNOGS Network API to GET jobs."""
    gps_locator = locator.Locator()
    gps_locator.update_location()
    LOGGER.debug('Get jobs started')
    url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'jobs/')
    params = {
        'ground_station': settings.SATNOGS_STATION_ID,
        'lat': settings.SATNOGS_STATION_LAT,
        'lon': settings.SATNOGS_STATION_LON,
        'alt': int(settings.SATNOGS_STATION_ELEV)
    }
    headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}
    LOGGER.debug('URL: %s', url)
    LOGGER.debug('Params: %s', params)
    LOGGER.debug('Headers: %s', headers)
    LOGGER.info('Trying to GET observation jobs from the network')
    try:
        response = requests.get(url,
                                params=params,
                                headers=headers,
                                verify=settings.SATNOGS_VERIFY_SSL,
                                timeout=45)
    except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects):
        LOGGER.exception('An error occurred trying to GET observation jobs from network')

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_error:
        LOGGER.error(http_error)
        return

    latest_jobs = [str(job['id']) for job in response.json()]
    for job in SCHEDULER.get_jobs():
        if job.name == spawn_observer.__name__:
            if job.id not in latest_jobs:
                job.remove()

    for obj in response.json():
        start = parser.parse(obj['start'])
        job_id = str(obj['id'])
        kwargs = {'obj': obj}
        LOGGER.debug('Adding new job: %s', job_id)
        LOGGER.debug('Observation obj: %s', obj)
        SCHEDULER.add_job(spawn_observer,
                          'date',
                          run_date=start,
                          id='{0}'.format(job_id),
                          kwargs=kwargs,
                          replace_existing=True)


def status_listener():
    LOGGER.info('Starting scheduler...')
    SCHEDULER.start()
    SCHEDULER.remove_all_jobs()
    LOGGER.info('Registering `get_jobs` periodic task (%d sec. interval)',
                settings.SATNOGS_NETWORK_API_QUERY_INTERVAL)
    SCHEDULER.add_job(get_jobs,
                      'interval',
                      seconds=settings.SATNOGS_NETWORK_API_QUERY_INTERVAL,
                      next_run_time=datetime.now(pytz.utc))
    LOGGER.info('Registering `post_data` periodic task (%d sec. interval)',
                settings.SATNOGS_NETWORK_API_POST_INTERVAL)
    SCHEDULER.add_job(post_data, 'interval', seconds=settings.SATNOGS_NETWORK_API_POST_INTERVAL)
