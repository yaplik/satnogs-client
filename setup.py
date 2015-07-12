from setuptools import find_packages, setup


setup(name='satnogsclient',
      packages=find_packages(),
      version='0.2.3',
      author='SatNOGS team',
      author_email='client-dev@satnogs.org',
      url='https://github.com/satnogs/satnogs-client/',
      description='SatNOGS Client',
      install_requires=['APScheduler',
                        'SQLAlchemy',
                        'requests',
                        'validators',
                        'python-dateutil',
                        'ephem',
                        'pytz'],
      dependency_links=[
          'git+https://github.com/brandon-rhodes/pyephem.git@47d0ba3616ee6c308f2eed319af3901592d00f70#egg=ephem'
      ],
      scripts=['satnogsclient/bin/satnogs-poller',
               'satnogsclient/bin/satnogs-task'])
