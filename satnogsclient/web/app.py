from flask import Flask, render_template, json, jsonify
from flask.ext.socketio import SocketIO, emit
from multiprocessing import Process

from satnogsclient import settings as client_settings
from satnogsclient.upsat import packet, tx_handler, packet_settings, large_data_service

from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.scheduler import tasks
import logging
import os


logger = logging.getLogger('satnogsclient')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, message_queue='redis://')


@app.route('/update_status', methods=['GET', 'POST'])
def get_status_info():
    current_pass_json = {}
    scheduled_pass_json = {}
    current_pass_json['azimuth'] = 'NA'
    current_pass_json['altitude'] = 'NA'
    current_pass_json['frequency'] = 'NA'
    current_pass_json['tle0'] = 'NA'
    current_pass_json['tle1'] = 'NA'
    current_pass_json['tle2'] = 'NA'
    # current_pass_json = jsonify(current_pass_json)
    scheduled_pass_json['Info'] = 'There are no scheduled observations.'
    # scheduled_pass_json = jsonify(scheduled_pass_json)

    current_pass_sock = Commsocket('127.0.0.1', client_settings.CURRENT_PASS_TCP_PORT)
    scheduled_pass_sock = Commsocket('127.0.0.1', client_settings.TASK_FEEDER_TCP_PORT)

    current_pass_check = current_pass_sock.connect()
    scheduled_pass_check = scheduled_pass_sock.connect()

    if scheduled_pass_check:
        scheduled_pass_json = scheduled_pass_sock.send("Requesting scheduled observations\n")
        scheduled_pass_json = json.loads(scheduled_pass_json)
    else:
        logger.info('No observation currently')

    if current_pass_check:
        current_pass_json = current_pass_sock.send("Requesting current observations\n")
        current_pass_json = json.loads(current_pass_json)
    else:
        logger.info('No observation currently')

    # return current_pass_json
    return jsonify(observation=dict(current=current_pass_json, scheduled=scheduled_pass_json))


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


@socketio.on('schedule_observation', namespace='/manual_observation')
def handle_observation(data):
    logger.info('Received manual observation: ' + str(data))
    requested_command = json.loads(data)
    # handle received observation
    if json is not None:
        dict_out = {'tle0': requested_command['tle0'],
                    'tle1': requested_command['tle1'],
                    'tle2': requested_command['tle2'],
                    'start': requested_command['start_time'],
                    'end': requested_command['end_time'],
                    'frequency': requested_command['freq'],
                    'id': requested_command['obs_id'],
                    'mode': requested_command['mode']}
        tasks.add_observation(dict_out)


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
            response = {'id': 1, 'log_message': 'ECSS command send', 'command_sent': ecss}
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
                    response = {'id': 1, 'log_message': 'COMMS_OFF command sent'}
                elif requested_command['custom_cmd']['comms_tx_rf'] == 'comms_on':
                    packet.comms_on()
                    response = {'id': 1, 'log_message': 'COMMS_ON command sent'}
                emit('backend_msg', response)


if __name__ == '__main__':
    socketio.run(app)
