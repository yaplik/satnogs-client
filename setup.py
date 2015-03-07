from setuptools import setup


setup(name='SatNOGS client',
      packages=['satnogsclient'],
      version='0.1',
      description='SatNOGS Client',
      install_requires=['APScheduler',
                        'SQLAlchemy',
                        'requests',
                        'validators',
                        'python-dateutil',
                        'pyephem'],
      scripts=['satnogsclient/bin/satnogs-poller'])
