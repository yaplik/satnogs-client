# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime, timedelta
from dateutil import parser
from urlparse import urljoin

import pytz
import requests

from satnogsclient import settings
from satnogsclient.observer.observer import Observer
from satnogsclient.receiver import SignalReceiver
from satnogsclient.scheduler import scheduler


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

    setup = observer.setup(**setup_kwargs)

    if setup:
        observer.observe()
    else:
        raise RuntimeError('Error in observer setup.')


def spawn_receiver(*args, **kwargs):
    obj = kwargs.pop('obj')
    receiver = SignalReceiver(obj['id'], obj['frequency'])
    receiver.run()
    end = parser.parse(obj['end'])

    while True:
        if datetime.now(pytz.utc) < end:
            time.sleep(1)
        else:
            receiver.stop()
            sys.exit()


def post_data():
    """PUT observation data back to Network API."""
    base_url = urljoin(settings.NETWORK_API_URL, 'data/')
    headers = {'Authorization': 'Token {0}'.format(settings.API_TOKEN)}
    for root, dirs, files in os.walk(settings.OUTPUT_PATH):
        for f in files:
            observation_id = f.split('_')[1]
            observation = {'payload': open(f, 'rb')}
            url = urljoin(base_url, observation_id)
            response = requests.put(url, headers=headers, files=observation)
            if response.status_code == 200:
                dst = os.path.join(settings.COMPLETE_OUTPUT_PATH, f)
            else:
                dst = os.path.join(settings.INCOMPLETE_OUTPUT_PATH, f)
            os.rename(f, dst)


def get_jobs():
    """Query SatNOGS Network API to GET jobs."""

    url = urljoin(settings.NETWORK_API_URL, 'jobs')
    params = {'ground_station': settings.GROUND_STATION_ID}
    headers = {'Authorization': 'Token {0}'.format(settings.API_TOKEN)}
    response = requests.get(url, params=params, headers=headers, verify=settings.VERIFY_SSL)

    if not response.status_code == 200:
        raise Exception('Status code: {0} on request: {1}'.format(response.status_code, url))

    for job in scheduler.get_jobs():
        if job.name in [spawn_observer.__name__, spawn_receiver.__name__]:
            job.remove()

    for obj in response.json():
        start = parser.parse(obj['start'])
        job_id = str(obj['id'])
        kwargs = {'obj': obj}
        receiver_start = start - timedelta(seconds=settings.DEMODULATOR_INIT_TIME)
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
