#!/usr/bin/env python
import logging

from satnogsclient.scheduler.tasks import status_listener, exec_rigctld
import threading
import time

logger = logging.getLogger('satnogsclient')


def main():

    logger.info('Starting status listener thread...')
    ser = threading.Thread(target=status_listener, args=())
    ser.daemon = True
    ser.start()
    exec_rigctld()
    logger.info('Press Ctrl+C to exit SatNOGS poller')
    while True:
        time.sleep(10)


if __name__ == '__main__':
    main()
