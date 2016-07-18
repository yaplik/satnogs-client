from flask import Flask, render_template, request, json, jsonify


from satnogsclient import settings as client_settings
from satnogsclient.upsat import packet, tx_handler
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.udpsocket import Udpsocket
import logging
import cPickle
import os

logger = logging.getLogger('satnogsclient')
app = Flask(__name__)


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


@app.route('/control_rx', methods=['GET', 'POST'])
def get_control_rx():
    if int(os.environ['ECSS_FEEDER_PID']) == 0:
        tmp = {}
        tmp['log_message'] = 'ECSS feeder thread not online'
        return jsonify(tmp)
    sock = Udpsocket(('127.0.0.1', client_settings.CLIENT_LISTENER_UDP_PORT))
    packet_list = ""
    try:
        conn = sock.send_listen("Requesting received packets", ('127.0.0.1', client_settings.ECSS_FEEDER_UDP_PORT))
        data = conn[0]
    except Exception as e:
        logger.error("An error with the ECSS feeder occured")
        logger.error(e)
        tmp = {}
        tmp['log_message'] = e
        return jsonify(tmp)
    logger.info("Packet: %s", data)
    packet_list = cPickle.loads(data)
    """
    The received 'packet_list' is a json string containing packets. Actually it is a list of dictionaries:
    each dictionary has the ecss fields of the received packet. In order to get each dictionary 2 things must be done
    The first json.loads(packet_list) will give a list of json strings representing the dictionaries.
    Next, for each item in list, json.dumps(item) will give the ecss dictionary
    """
    ecss_dicts = {}
    if packet_list:
        cnt = 0
        for str_dict in packet_list:
            ecss_dict = cPickle.loads(str_dict)
            logger.info("Received ECSS formated: %d", ecss_dict)
            res = packet.ecss_logic(ecss_dict)
            ecss_dicts[cnt] = res
            cnt += 1
        logger.info("Shipping: %d", ecss_dicts)
        return jsonify(ecss_dicts)
    else:
        tmp = {}
        tmp[0] = {'log_message': 'backend_online'}
        return jsonify(tmp)


@app.route('/command', methods=['GET', 'POST'])
def get_command():
    requested_command = request.get_json()
    response = {}
    response[0] = {'id': 1, 'log_message': 'This is a test response'}
    if requested_command is not None:
        if 'custom_cmd' in requested_command:
            if 'comms_tx_rf' in requested_command['custom_cmd']:
                # TODO: Handle the comms_tx_rf request
                if requested_command['custom_cmd']['comms_tx_rf'] == 'comms_off':
                    packet.comms_off()
                    response[0] = {'id': 1, 'log_message': 'COMMS_OFF command sent'}
                    return jsonify(response)
                elif requested_command['custom_cmd']['comms_tx_rf'] == 'comms_on':
                    packet.comms_on()
                    response[0] = {'id': 1, 'log_message': 'COMMS_ON command sent'}
                    return jsonify(response)
            elif 'mode' in requested_command['custom_cmd']:
                # TODO: Handle the comms_tx_rf request
                mode = requested_command['custom_cmd']['mode']
                if requested_command['custom_cmd']['mode'] == 'cmd_ctrl':
                    response[0] = {'log_message': 'Mode changed to Stand-Alone'}
                    response[0] = {'id': 1}
                    # return jsonify(response)
                elif requested_command['custom_cmd']['mode'] == 'network':
                    response[0] = {'id': 1, 'log_message': 'Mode changed to Network'}
                    # return jsonify(response)
                dict_out = {'mode': mode}
                packet.custom_cmd_to_backend(dict_out)
            elif 'backend' in requested_command['custom_cmd']:
                # TODO: Handle the comms_tx_rf request
                backend = requested_command['custom_cmd']['backend']
                if requested_command['custom_cmd']['backend'] == 'gnuradio':
                    response[0] = {'id': 1, 'log_message': 'Backend changed to GNURadio'}
                    # return jsonify(response)
                elif requested_command['custom_cmd']['backend'] == 'serial':
                    response[0] = {'id': 1, 'log_message': 'Backend changed to Serial'}
                    # return jsonify(response)
                dict_out = {'backend': backend}
                packet.custom_cmd_to_backend(dict_out)
        elif 'ecss_cmd' in requested_command:
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
            response[0] = {'id': 1, 'log_message': 'ECSS command send'}
            tx_handler.send_to_backend(buf)
            return jsonify(response)
    return render_template('upsat_control.j2')


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
