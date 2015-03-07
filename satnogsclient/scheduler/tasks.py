# -*- coding: utf-8 -*-
from urlparse import urljoin

import requests

from dateutil import parser

from satnogsclient import settings
from satnogsclient.scheduler import scheduler


def spawn_observation(*args, **kwargs):
    raise NotImplementedError


def get_jobs():
    """Query SatNOGS Network API to GET jobs."""
    url = urljoin(settings.NETWORK_API_URL, 'jobs')
    params = {'ground_station': settings.GROUND_STATION_ID}
    response = requests.get(url, params=params)

    if not response.status_code == 200:
        raise Exception('Status code: {0} on request: {1}'.format(response.status_code, url))

    for job in scheduler.get_jobs():
        if job.name == spawn_observation.__name__:
            job.remove()

    for obj in response.json():
        start = parser.parse(obj['start'])
        job_id = str(obj['id'])
        scheduler.add_job(spawn_observation, 'date', run_date=start, id=job_id, kwargs=obj)
