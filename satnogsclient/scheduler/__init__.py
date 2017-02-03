# -*- coding: utf-8 -*-
from pytz import utc

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from satnogsclient import settings


jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SATNOGS_SQLITE_URL)
}

executors = {
    'default': ThreadPoolExecutor(20),
}

job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 5
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults,
                                timezone=utc)
