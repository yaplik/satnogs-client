from __future__ import absolute_import, division, print_function

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

JOBSTORES = {'default': MemoryJobStore()}

EXECUTORS = {
    'default': ThreadPoolExecutor(20),
}

JOB_DEFAULTS = {'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 30}

SCHEDULER = BackgroundScheduler(jobstores=JOBSTORES,
                                executors=EXECUTORS,
                                job_defaults=JOB_DEFAULTS,
                                timezone=utc)
