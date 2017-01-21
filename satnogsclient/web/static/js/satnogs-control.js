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

  manual_observation_socket.on('backend_msg', function(data) {
      console.log(data);
      if (data.response_type == 'init' || data.response_type == 'obs_success') {
        append_manual_obs_list(data.scheduled_observation_list);
      } else if (data.response_type == 'obs_end') {
          var obs_id = parseInt(data.id, 0);
          remove_manual_obs_list(obs_id);
      }
  });

  $("#mode-switch li").click(function() {
      var current_mode = Cookies.get('mode');
      if (current_mode === null || typeof current_mode == 'undefined') {
          current_mode = 'network';
          Cookies.set('mode', current_mode);
      }
      display_control_view(current_mode);
  });

  $('#UTCModal').on('show.bs.modal', function (e) {
      $('#timezone-utc').text(moment().utc().format("HH:mm:ss"));
      $('#timezone-local').text(moment().format("HH:mm:ss"));
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
      format: 'YYYY-MM-DD HH:mm',
      timeZone: 'UTC',
  });

  datetimepicker_end = $('#gs-cnc-end').datetimepicker({
      format: 'YYYY-MM-DD HH:mm',
      timeZone: 'U',
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
  var mode = $("#gs-cnc-mode").val();
  var start_time = datetimepicker_start.data("DateTimePicker").date().utc().add(datetimepicker_start.data("DateTimePicker").date().utcOffset(), 'm').format();
  var end_time = datetimepicker_end.data("DateTimePicker").date().utc().add(datetimepicker_end.data("DateTimePicker").date().utcOffset(), 'm').format();

  var msg = {};
  msg.tle0 = tle0;
  msg.tle1 = tle1;
  msg.tle2 = tle2;
  msg.freq = freq;
  msg.mode = mode;
  msg.start_time = start_time;
  msg.end_time = end_time;

  var json_packet = JSON.stringify(msg);
  console.log(json_packet);
  return json_packet;

}

function append_manual_obs_list(obs_list) {
    for (var i = 0; i < obs_list.length; i++) {
        var obs_id = obs_list[i].id;
        var mode = obs_list[i].mode;
        var freq = obs_list[i].frequency;
        var start_time = moment(obs_list[i].start).format("YYYY-MM-DD HH:mm");
        var end_time = moment(obs_list[i].end).format("YYYY-MM-DD HH:mm");
        $("#scheduled_obs_table").find('tbody')
            .append($('<tr>')
                .append($('<td>' + obs_id + '</td>' +
                      '<td>' + freq + '</td>'  +
                      '<td>' + mode + '</td>'  +
                      '<td>' + start_time + ' - ' + end_time +'</td>'))
            );
    }
}

function remove_manual_obs_list(obs_id) {
    $('#scheduled_obs_table tbody tr td:first-child').each(function() {
        if (parseInt($(this).text(), 0) == obs_id) {
            $(this).parent().remove();
        }
    });
}
