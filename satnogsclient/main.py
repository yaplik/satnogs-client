#!/usr/bin/env python
import logging

from satnogsclient.scheduler.tasks import status_listener, exec_rigctld
from satnogsclient.web.app import app, socketio
from satnogsclient.upsat.packet import folder_init
import threading

logger = logging.getLogger('satnogsclient')


def main():

    logger.info('Starting status listener thread...')
    ser = threading.Thread(target=status_listener, args=())
    ser.daemon = True
    ser.start()
    folder_init()
    exec_rigctld()
    try:
        logger.info('Press Ctrl+C to exit SatNOGS poller')
        socketio.run(app, host='0.0.0.0')
    except (KeyboardInterrupt, SystemExit):
        socketio.stop()


if __name__ == '__main__':
    main()
