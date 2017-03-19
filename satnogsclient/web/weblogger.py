import logging
from flask_socketio import SocketIO

socketio = SocketIO(message_queue='redis://')


class WebLogger(logging.Logger):

    def __init__(self, name, level=logging.NOTSET):
        return super(WebLogger, self).__init__(name, level)

    def info(self, msg, *args, **kwargs):
        ''' TODO: Remove happy-hacky work around to avoid socketio polling'''
        if "socket.io" not in msg:
            dict_out = {'type': 'info', 'log_message': msg}
            socketio.emit('update_console', dict_out, namespace='/update_status')
        return super(WebLogger, self).info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        dict_out = {'type': 'debug', 'log_message': msg}
        socketio.emit('update_console', dict_out, namespace='/update_status')
        return super(WebLogger, self).debug(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        dict_out = {'type': 'error', 'log_message': msg}
        socketio.emit('update_console', dict_out, namespace='/update_status')
        return super(WebLogger, self).error(msg, *args, **kwargs)
