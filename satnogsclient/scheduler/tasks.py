# -*- coding: utf-8 -*-
import logging
import os
import time
import sys
from datetime import datetime, timedelta
from dateutil import parser
from urlparse import urljoin
from multiprocessing import Process, Queue
import json

import pytz
import requests

from satnogsclient import settings
from satnogsclient.observer.observer import Observer
from satnogsclient.receiver import SignalReceiver
from satnogsclient.scheduler import scheduler
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.udpsocket import Udpsocket
from time import sleep



logger = logging.getLogger('satnogsclient')


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
            
    sock = Commsocket('127.0.0.1',client_settings.TASK_LISTENER_TCP_PORT)
    
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
        print 'Task listener thread not online'
    
        
def task_feeder(port1,port2):
    sleep(1)
    logger.info('Started task feeder')
    print port1,' ',port2
    sock = Commsocket('127.0.0.1',port1)
    sock.bind()
    q = Queue(maxsize=1)
    p = Process(target=task_listener, args=(port2,q))
    p.daemon = True
    p.start()
    sock.listen()
    while 1:
        conn = sock.accept()
        if conn:
            data = conn.recv(sock.tasks_buffer_size)
            if not q.empty():
                conn.send(q.get())
            else:
                conn.send('[]')
    p.join()

    
def task_listener(port,queue):
    logger.info('Started task listener')
    print port
    sock = Commsocket('127.0.0.1',port)
    sock.bind()
    sock.listen()
    while 1:
        conn = sock.accept()
        if conn:
            data = conn.recv(sock.tasks_buffer_size)
            if not queue.empty():
                queue.get()
                queue.put(data)
            else:
                queue.put(data)

def ecss_feeder(port1,port2):
    sleep(1)
    logger.info('Started ecss feeder')
    print port1,' ',port2
    sock = Udpsocket(('127.0.0.1',port1))    
    qu = Queue(maxsize=10)
    pr = Process(target=ecss_listener, args=(port2,qu))
    pr.daemon = True
    pr.start()
    while 1:
        conn = sock.recv()
        list= []
        while not qu.empty():
            a = qu.get()
            list.append(a)
        sock.sendto(json.dumps(list),conn[1])     
    pr.join()

    
def ecss_listener(port,queue):
    logger.info('Started ecss listener')
    sock = Udpsocket(('127.0.0.1',port))
    while 1:
            conn = sock.recv()
            data = conn[0]
            if not queue.empty():
                queue.put(data)
            else:
                queue.put(data)         
