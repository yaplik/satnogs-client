from setuptools import find_packages, setup


setup(name='SatNOGS client',
      packages=find_packages(),
      version='0.1',
      description='SatNOGS Client',
      install_requires=['APScheduler',
                        'SQLAlchemy',
                        'requests',
                        'validators',
                        'python-dateutil',
                        'pyephem',
                        'pytz'],
      scripts=['satnogsclient/bin/satnogs-poller',
               'satnogsclient/bin/satnogs-task'])
