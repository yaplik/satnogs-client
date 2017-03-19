from setuptools import find_packages, setup


setup(
    name='satnogsclient',
    version='0.2.5',
    url='https://github.com/satnogs/satnogs-client/',
    author='SatNOGS team',
    author_email='client-dev@satnogs.org',
    description='SatNOGS Client',
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
        'pyopenssl',
        'pyserial',
        'flask-socketio',
        'redis'
    ],
    extras_require={
        'develop': 'flake8'
    },
    entry_points={
        'console_scripts': ['satnogs-client=satnogsclient.main:main'],
    },
    include_package_data=True,
    packages=find_packages()
)
