from setuptools import find_packages, setup


setup(name='satnogsclient',
      packages=find_packages(),
      version='0.2.5',
      author='SatNOGS team',
      author_email='client-dev@satnogs.org',
      url='https://github.com/satnogs/satnogs-client/',
      description='SatNOGS Client',
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'APScheduler',
          'SQLAlchemy',
          'requests',
          'validators',
          'python-dateutil',
          'ephem',
          'pytz',
          'flask',
          'pyopenssl'
      ],
      scripts=['satnogsclient/bin/satnogs-poller',
               'satnogsclient/bin/satnogs-task'])
