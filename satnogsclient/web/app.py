from flask import Flask, render_template, json
from flask_socketio import SocketIO, emit
from multiprocessing import Process

from satnogsclient import settings as client_settings
from satnogsclient.upsat import packet, tx_handler, packet_settings, large_data_service
from satnogsclient.scheduler import tasks
from satnogsclient.web.weblogger import WebLogger
import logging
import os
import fnmatch

logging.setLoggerClass(WebLogger)
logger = logging.getLogger('default')
assert isinstance(logger, WebLogger)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, message_queue='redis://')


@socketio.on('connect', namespace='/update_status')
def send_status():
    dict_out = {'id': client_settings.SATNOGS_STATION_ID,
                'coord': str(round(client_settings.SATNOGS_STATION_LAT, 1)) + '-' + str(round(client_settings.SATNOGS_STATION_LON, 1)),
                'alt': str(client_settings.SATNOGS_STATION_ELEV)}
    emit('init_status', dict_out)
    logger.info("Status view initiated")
    response = {}
    scheduled_jobs = tasks.get_observation_list()
    obs_list = []
    for job in scheduled_jobs:
        if 'obj' in job.kwargs:
            obs_list.append(job.kwargs['obj'])
    response['scheduled_observation_list'] = obs_list
    emit('update_scheduled', response)


@app.route('/')
def status():
    '''View status satnogs-client.'''
    return render_template('status.j2')


@app.route('/upsat_control/')
def upsat_control():
    '''UPSat command and control view.'''
    return render_template('upsat_control.j2')


@app.route('/satnogs_control/')
def satnogs_control():
    '''Satnogs command and control view.'''
    return render_template('satnogs_control.j2')


@app.route('/configuration/')
def configuration():
    '''View list of satnogs-client settings.'''
    filters = [
        lambda x: not x.startswith('_'),
        lambda x: x.isupper()
    ]

    entries = client_settings.__dict__.items()
    settings = filter(lambda (x, y): all(f(x) for f in filters), entries)

    ctx = {
        'settings': sorted(settings, key=lambda x: x[0])
    }

    return render_template('configuration.j2', **ctx)


@socketio.on('mode_change', namespace='/config')
def handle_mode_change(data):
    logger.info('Received mode change: ' + str(data))
    requested_command = json.loads(data)
    if json is not None:
        if 'custom_cmd' in requested_command:
            if 'mode' in requested_command['custom_cmd']:
                mode = requested_command['custom_cmd']['mode']
                dict_out = {'mode': mode}
                packet.custom_cmd_to_backend(dict_out)
                emit('backend_msg', dict_out)


@socketio.on('backend_change', namespace='/config')
def handle_backend_change(data):
    logger.info('Received backend change: ' + str(data))
    requested_command = json.loads(data)
    if json is not None:
        if 'custom_cmd' in requested_command:
            if 'backend' in requested_command['custom_cmd']:
                backend = requested_command['custom_cmd']['backend']
                dict_out = {'backend': backend}
                packet.custom_cmd_to_backend(dict_out)
                emit('backend_msg', dict_out)


@socketio.on('connect', namespace='/manual_observation')
def init_observation_table():
    logger.info("Satnogs control view initiated")
    response = {}
    response['response_type'] = 'init'
    scheduled_jobs = tasks.get_observation_list()
    obs_list = []
    for job in scheduled_jobs:
        if 'obj' in job.kwargs:
            obs_list.append(job.kwargs['obj'])
    response['scheduled_observation_list'] = obs_list
    emit('backend_msg', response)
    flowgraphs = []
    for path in client_settings.GNURADIO_SCRIPT_PATH:
        for root, dirs, files in os.walk(path):
            for name in files:
                if fnmatch.fnmatch(name, 'satnogs_*.py'):
                    flowgraphs.append(name)
    response['scripts'] = flowgraphs
    emit('update_script_names', response)


@socketio.on('schedule_observation', namespace='/manual_observation')
def handle_observation(data):
    logger.info('Received manual observation: ' + str(data))
    requested_command = json.loads(data)
    # handle received observation
    scheduled_jobs = tasks.get_observation_list()
    # Assign next biggest available observation id
    if not scheduled_jobs:
        obs_id = 1
    else:
        obs_id = int(scheduled_jobs[len(scheduled_jobs) - 1].id) + 1

    if json is not None:
        dict_out = {'tle0': requested_command['tle0'],
                    'tle1': requested_command['tle1'],
                    'tle2': requested_command['tle2'],
                    'start': requested_command['start_time'],
                    'end': requested_command['end_time'],
                    'id': obs_id,
                    'script_name': requested_command['script_name'],
                    'user_args': requested_command['user_args']
                    }
        logger.info(dict_out)
        obs = tasks.add_observation(dict_out)
        if obs is not None:
            response = {}
            response['response_type'] = 'obs_success'
            obs_list = []
            obs_list.append(obs.kwargs['obj'])
            response['scheduled_observation_list'] = obs_list
            emit('backend_msg', response)
        else:
            logger.info('Error adding observation')


@socketio.on('ecss_command', namespace='/cmd')
def handle_requested_cmd(data):
    logger.info('Received backend change: ' + str(data))
    response = {'id': 1, 'log_message': 'This is a test response'}
    requested_command = json.loads(data)
    if json is not None:
        if 'ecss_cmd' in requested_command:
            logger.info('Received ECSS packet from UI')
            ecss = {'app_id': int(requested_command['ecss_cmd']['PacketHeader']['PacketID']['ApplicationProcessID']),
                    'type': int(requested_command['ecss_cmd']['PacketHeader']['PacketID']['Type']),
                    'size': len(requested_command['ecss_cmd']['PacketDataField']['ApplicationData']),
                    'seq_count': 0,
                    'ser_type': int(requested_command['ecss_cmd']['PacketDataField']['DataFieldHeader']['ServiceType']),
                    'ser_subtype': int(requested_command['ecss_cmd']['PacketDataField']['DataFieldHeader']['ServiceSubType']),
                    'data': map(int, requested_command['ecss_cmd']['PacketDataField']['ApplicationData']),
                    'dest_id': int(requested_command['ecss_cmd']['PacketDataField']['DataFieldHeader']['SourceID']),
                    'ack': int(requested_command['ecss_cmd']['PacketDataField']['DataFieldHeader']['Ack'])}

            # check if ui wants a specific seq count
            if 'SequenceCount' in requested_command['ecss_cmd']['PacketHeader']['PacketSequenceControl']:
                logger.info('Seq count from ui')
            # store packet for response check
            if ecss['ack'] == '1':
                logger.info('Storing packet for verification')

            buf = packet.construct_packet(ecss, os.environ['BACKEND'])
            response = {
                'id': 1, 'log_message': 'ECSS command send', 'command_sent': ecss}
            if len(buf) > packet_settings.MAX_COMMS_PKT_SIZE:
                ld = Process(target=large_data_service.uplink, args=(buf,))
                ld.daemon = True
                ld.start()
            else:
                tx_handler.send_to_backend(buf)

            emit('backend_msg', response)


@socketio.on('comms_switch_command', namespace='/cmd')
def handle_comms_switch_cmd(data):
    logger.info('Received backend change: ' + str(data))
    response = {'id': 1, 'log_message': 'This is a test response'}
    requested_command = json.loads(data)
    if requested_command is not None:
        if 'custom_cmd' in requested_command:
            if 'comms_tx_rf' in requested_command['custom_cmd']:
                # TODO: Handle the comms_tx_rf request
                if requested_command['custom_cmd']['comms_tx_rf'] == 'comms_off':
                    packet.comms_off()
                    response = {
                        'id': 1, 'log_message': 'COMMS_OFF command sent'}
                elif requested_command['custom_cmd']['comms_tx_rf'] == 'comms_on':
                    packet.comms_on()
                    response = {
                        'id': 1, 'log_message': 'COMMS_ON command sent'}
                emit('backend_msg', response)


if __name__ == '__main__':
    socketio.run(app)
