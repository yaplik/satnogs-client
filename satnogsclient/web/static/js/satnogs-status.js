function update_scheduled_obs(json_data) {
    var response_panel = $('#scheduled-obs-frame');
    response_panel.html('<table class="table table-hover"><thead><tr>' +
                      '<th>ID</th><th>Satellite</th><th>Frequency</th>' +
                      '<th>Encoding</th><th>Timeframe</th></tr></thead>' +
                      '<tbody></tbody></table>');
    var response_panel_table = $('#scheduled-obs-frame table');

    var data = json_data;
    var data_length = json_data.length;
    for (var i = 0; i < data_length; i++) {
        if (data[i].frequency === "undefined") {
          frequency = '-';
        }
        else {
          frequency = data[i].frequency;
        }
        if (data[i].mode === "undefined") {
          mode = '-';
        }
        else {
          mode = data[i].mode;
        }
        response_panel_table.append('<tr><td>' + data[i].id + '</td>' +
            '<td>' + data[i].tle0 + '</td>' +
            '<td>' + frequency + '</td>' +
            '<td>' + mode + '</td>' +
            '<td>' + data[i].start + '-' + data[i].end + '</td>' +
            '</tr>');
    }
}

function update_current_obs(json_data) {
  var table_obs = $('#current-obs');
  table_obs.html('<table class="table"><thead><tr><th>ID</th><th>Satellite</th>' +
                '<th>Frequency</th><th>Encoding</th><th>Rise Time</th><th>Max Altitude</th>' +
                '<th>Rising Azimuth</th><th>Elevation</th></tr></thead><tbody></tbody></table>');
}

function init_status_view(json_data) {

    var gs_id = $('#gs-id');
    var gs_coord = $('#gs-coord');
    var gs_alt = $('#gs-alt');
    var gs_freq = $('#gs-freq');
    var gs_azim = $('#gs-azim');
    var gs_elev = $('#gs-elev');
    gs_id.text(json_data.id);
    gs_coord.text(json_data.coord);
    gs_alt.text(json_data.alt);
    gs_freq.text("-");
    gs_azim.text("-");
    gs_elev.text("-");

    var table_obs = $('#current-obs');
    table_obs.css('text-align','center');
    table_obs.html('No active observation');
}

function update_rotator(json_data) {
    var gs_azim = $('#gs-azim');
    var gs_elev = $('#gs-elev');
    var gs_freq = $('#gs-freq');
    gs_azim.text(json_data.azimuth);
    gs_elev.text(json_data.altitude);
    gs_freq.text(json_data.frequency);
}

function print_log(data) {
    var response_panel = $('#response-panel-body ul');
    var data_type;
    var resp = data;
    console.log(data);
    if (resp.type == 'debug') {
        data_type = "debug";
        log_data = resp.log_message;
        to_log = '<span class="label label-warning">[DEBUG]:</span>';
    } else if (resp.type == 'error') {
        data_type = "error";
        log_data = resp.log_message;
        to_log = '<span class="label label-danger">[ERROR]:</span>';
    } else if (resp.type == 'info') {
        data_type = "info";
        log_data = resp.log_message;
        to_log = '<span class="label label-info">[INFO]:</span>';
    }

    response_panel.append('<li class="' + apply_log_filter(data_type) + '"' + ' data-type="' + data_type + '">' +
        '<span class="label label-default" title="' + moment().format('YYYY/MM/DD').toString() + '">' + moment().format('HH:mm:ss').toString() +
        '</span>' + to_log + ' ' + log_data + '</li>');

    $('#response-panel-body').scrollTop(response_panel.height());

}
//A function that returns the appropriate class based on the applied filters
function apply_log_filter(log_data_type) {
    var status = $('#filter-section :input[value=' + log_data_type + ']').is(':checked');
    if (status) {
        return 'show-log';
    } else {
        return 'hide-log';
    }
}

// A function that parses the log console, generates a string and saves it on a CSV file.
function log_console_save() {
    str = '';
    var log_content = [];
    var strArray = [];
    $('#log-list li').each(function(i) {
        // Retrieve all the child nodes of the log list element
        log_content = $.makeArray($(this)[0].childNodes);
        // Construct a string array with the containing values
        for (j = 0; j < log_content.length; j++) {
            // Check the type of the element for appropriate handling
            if ($(log_content[j]).is('span')) {
                strArray.push(log_content[j].innerText);
            } else {
                strArray.push(log_content[j].data);
            }
        }
        // Encode each log message into CSV
        str += csv_encode(strArray);
        str += '\n';
        log_content = [];
        strArray = [];
    });
    var blob = new Blob([str], {
        type: "text/csv;charset=utf-8"
    });
    saveAs(blob, "upsat_cnc_log.csv");
}

function csv_encode(strArray) {
    csv_str = '';
    $.each(strArray, function(index, value) {
        csv_str += value;
        if (index < strArray.length - 1) {
            csv_str += ';';
        }
    });
    return csv_str;
}


// Initialize status page
$(document).ready(function() {
    var status_socket = io.connect('http://' + document.domain + ':' + location.port + '/update_status', {
        rememberTransport: false,
        'reconnect': true,
        'reconnection delay': 500,
        'max reconnection attempts': 10
    });

    status_socket.on('init_status', function(data) {
      init_status_view(data);
    });

    status_socket.on('update_scheduled', function(data) {
      update_scheduled_obs(data.scheduled_observation_list);
    });

    status_socket.on('update_console', function(data) {
      print_log(data);
    });

    status_socket.on('update_rotator', function(data) {
      console.log("hey");
      console.log(data);
      update_rotator(data);
    });

    $('#filter-section input').on('change', function() {
        var itemsToFilter = $('#response-panel-body ul li');
        for (var i = 0; i < itemsToFilter.length; i++) {
            var currentItem = itemsToFilter[i];
            if (currentItem.getAttribute("data-type") == $(this).val()) {
                if ($(this).is(':checked')) {
                    currentItem.classList.remove('hide-log');
                    currentItem.classList.add('show-log');
                } else {
                    currentItem.classList.remove('show-log');
                    currentItem.classList.add('hide-log');
                }
            }
        }
    });

    // Clear log
    $('#clear-log').on('click', function() {
        var itemsToFilter = $('#response-panel-body ul li');
        for (var i = 0; i < itemsToFilter.length; i++) {
            var currentItem = itemsToFilter[i];
            currentItem.remove();
        }
    });
    // Clear WOD Log
    $('#clear-wod-log').on('click', function() {
        var itemsToFilter = $('#response-panel-body-wod ul li');
        for (var i = 0; i < itemsToFilter.length; i++) {
            var currentItem = itemsToFilter[i];
            currentItem.remove();
        }
    });

    $('#save-log').on('click', function() {
        log_console_save();
    });

});
