from setuptools import find_packages, setup


setup(name='satnogsclient',
      packages=find_packages(),
      version='0.2.4',
      author='SatNOGS team',
      author_email='client-dev@satnogs.org',
      url='https://github.com/satnogs/satnogs-client/',
      description='SatNOGS Client',
      install_requires=[
          'APScheduler',
          'SQLAlchemy',
          'requests',
          'validators',
          'python-dateutil',
          'ephem',
          'pytz',
          'flask'
      ],
      scripts=['satnogsclient/bin/satnogs-poller',
               'satnogsclient/bin/satnogs-task'])
