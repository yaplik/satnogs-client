$(document).ready(function() {

    var manual_observation_socket = io.connect('http://' + document.domain + ':' + location.port + '/manual_observation', {
        rememberTransport: false,
        'reconnect': true,
        'reconnection delay': 500,
        'max reconnection attempts': 10
    });


    init();

    $('#gs-cnc-set-observation').on('click', function() {
        msg = encode_backend_message();
        manual_observation_socket.emit('schedule_observation', msg);
    });

    $("#mode-switch li").click(function() {
        var current_mode = Cookies.get('mode');
        if (current_mode === null || typeof current_mode == 'undefined') {
            current_mode = 'network';
            Cookies.set('mode', current_mode);
        }
        display_control_view(current_mode);
    });

});

function init() {
    current_mode = Cookies.get('mode');
    if (current_mode === null || typeof current_mode == 'undefined') {
        current_mode = "Network";
        Cookies.set('mode', current_mode);
    }

    display_control_view(current_mode);

    datetimepicker_start = $('#gs-cnc-start').datetimepicker({
        format: 'DD-MM-YYYY HH:mm:ss',
    });

    datetimepicker_end = $('#gs-cnc-end').datetimepicker({
        format: 'DD-MM-YYYY HH:mm:ss',
    });

}

function display_control_view(mode) {
    if (mode == 'Network') {
        // Disable Upsat Command and Control
        $('#gs-cnc').css('display', 'none');
        $('#backend-switch').css('display', 'none');
    } else if (mode == 'Stand-Alone') {
        // Enable Upsat Command and Control
        $('#gs-cnc').css('display', 'block');
        $('#backend-switch').css('display', 'block');
    }
}

function encode_backend_message() {
    var tle0 = $("#gs-cnc-tle0").val();
    var tle1 = $("#gs-cnc-tle1").val();
    var tle2 = $("#gs-cnc-tle2").val();
    var freq = $("#gs-cnc-freq").val();
    var obs_id = $("#gs-cnc-id").val();
    var mode = $("#gs-cnc-mode").val();
    var start_time = datetimepicker_start.data("DateTimePicker").date();
    var end_time = datetimepicker_end.data("DateTimePicker").date();

    var msg = {};
    msg.tle0 = tle0;
    msg.tle1 = tle1;
    msg.tle2 = tle2;
    msg.freq = freq;
    msg.obs_id = obs_id;
    msg.mode = mode;
    msg.start_time = start_time.utc();
    msg.end_time = end_time.utc();

    var json_packet = JSON.stringify(msg);
    console.log(json_packet);
    return json_packet;

}
