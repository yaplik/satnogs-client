$(document).ready(function() {

    init();

    $("#comms-gnu").click(function() {
        mode = "gnuradio";
        request = encode_backend_mode(mode);
        query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
        $("#comms-gnu").css('background-color', '#5cb85c');
        $("#comms-ser").css('background-color', '#d9534f');
    });

    $("#comms-ser").click(function() {
        mode = "serial";
        request = encode_backend_mode(mode);
        query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
        $("#comms-gnu").css('background-color', '#d9534f');
        $("#comms-ser").css('background-color', '#5cb85c');
    });


    $('#service-select li').on('click', function() {
        // Handle change on service parameter dropdowns
        selected_service_id = $(this).prop('id');
        $(this).addClass('active');
        display_service(selected_service_id);
    });

    $('#service-param-service_type').on('change', function() {
        // Handle change on service parameter dropdowns
        var subservice = $(this).find("option:selected").text();

        var VR_SERVICE = {
            TM_VR_ACCEPTANCE_SUCCESS: 1,
            TM_VR_ACCEPTANCE_FAILURE: 2
        };

        var HK_SERVICE = {
            TC_HK_REPORT_PARAMETERS: 21,
            TM_HK_PARAMETERS_REPORT: 23
        };

        var EV_SERVICE = {
            TM_EV_NORMAL_REPORT: 1,
            TM_EV_ERROR_REPORT: 4
        };

        var FM_SERVICE = {
            TC_FM_PERFORM_FUNCTION: 1
        };

        var SC_SERVICE = {
            TC_SC_ENABLE_RELEASE: 1,
            TC_SC_DISABLE_RELEASE: 2,
            TC_SC_RESET_SCHEDULE: 3,
            TC_SC_INSERT_TC: 4,
            TC_SC_DELETE_TC: 5,
            TC_SC_TIME_SHIFT_SPECIFIC: 7,
            TC_SC_TIME_SHIFT_SELECTED_OTP: 8,
            TC_SC_TIME_SHIFT_ALL: 15
        };

        var LD_SERVICE = {
            TM_LD_FIRST_DOWNLINK: 1,
            TC_LD_FIRST_UPLINK: 9,
            TM_LD_INT_DOWNLINK: 2,
            TC_LD_INT_UPLINK: 10,
            TM_LD_LAST_DOWNLINK: 3,
            TC_LD_LAST_UPLINK: 11,
            TC_LD_ACK_DOWNLINK: 5,
            TM_LD_ACK_UPLINK: 14,
            TC_LD_REPEAT_DOWNLINK: 6,
            TM_LD_REPEAT_UPLINK: 15,
            TM_LD_REPEATED_DOWNLINK: 7,
            TC_LD_REPEATED_UPLINK: 12,
            TM_LD_ABORT_SE_DOWNLINK: 4,
            TC_LD_ABORT_SE_UPLINK: 13,
            TC_LD_ABORT_RE_DOWNLINK: 8,
            TM_LD_ABORT_RE_UPLINK: 16
        };

        var MS_SERVICE = {
            TC_MS_ENABLE: 1,
            TC_MS_DISABLE: 2,
            TC_MS_CONTENT: 8,
            TC_MS_DOWNLINK: 9,
            TC_MS_DELETE: 11,
            TC_MS_REPORT: 12,
            TM_MS_CATALOGUE_REPORT: 13,
            TC_MS_UPLINK: 14,
            TC_MS_FORMAT: 15
        };

        var CT_SERVICE = {
            TC_CT_PERFORM_TEST: 1,
            TM_CT_REPORT_TEST: 2
        };

        var $select = $('#service-param-service_subtype');
        $select.find('option').remove();
        $select.append('<option selected="true" style="display:none;">Service sub Type</option>');

        var key;
        if (subservice == "TC_VERIFICATION_SERVICE") {
            for (key in VR_SERVICE) {
                $select.append('<option value=' + VR_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_HOUSEKEEPING_SERVICE") {
            for (key in HK_SERVICE) {
                $select.append('<option value=' + HK_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_EVENT_SERVICE") {
            for (key in EV_SERVICE) {
                $select.append('<option value=' + EV_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_FUNCTION_MANAGEMENT_SERVICE") {
            for (key in FM_SERVICE) {
                $select.append('<option value=' + FM_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_TIME_MANAGEMENT_SERVICE") {
            for (key in VR_SERVICE) {
                $select.append('<option value=' + VR_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_SCHEDULING_SERVICE") {
            for (key in SC_SERVICE) {
                $select.append('<option value=' + SC_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_LARGE_DATA_SERVICE") {
            for (key in LD_SERVICE) {
                $select.append('<option value=' + LD_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_MASS_STORAGE_SERVICE") {
            for (key in MS_SERVICE) {
                $select.append('<option value=' + MS_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_TEST_SERVICE") {
            for (key in CT_SERVICE) {
                $select.append('<option value=' + CT_SERVICE[key] + '>' + key + '</option>');
            }
        } else if (subservice == "TC_SU_MNLP_SERVICE") {
            for (key in VR_SERVICE) {
                $select.append('<option value=' + VR_SERVICE[key] + '>' + key + '</option>');
            }
        }
    });

    $('#service-param-time-report').on('change', function() {
        elem = document.getElementById('datetimepicker1');
        if ($('#service-param-time-report').find("option:selected").val() == "manual") {
            elem.style.display = "table";
        } else {
            elem.style.display = "none";
        }
    });

    $('#service-param-panel :button').on('click', function() {

        var list = $('this').parent().siblings().find('select');
        var selected_value = $('#service-select li.active a').text();
        //TODO: Check whether all required fields are selected
        var missing = [];
        var flag = true;
        for (i = 0; i < list.length; i++) {
            if (isNaN(list[i].value)) {
                missing.push(list[i].value);
                flag = false;
            }
        }

        if (selected_value == "Custom") {
            app_id = $('#service-param-app_id').val();
            type = $('#service-param-type').val();
            ack = $('#service-param-ack').val();
            service_type = $('#service-param-service_type').val();
            service_subtype = $('#service-param-service_subtype').val();
            dest_id = $('#service-param-dest_id').val();
            data = $('#service-param-service-data').val().split(",");
            seq_count = 0;
        } else if (selected_value == "House keeping") {
            app_id = $('#service-param-hk-app_id').val();
            type = 1;
            ack = 0;
            service_type = 3;
            service_subtype = 21;
            dest_id = $('#service-param-hk-dest-id').val();

            data = $('#service-param-hk-sid').val();


        } //else if (selected_value == "Mass storage") {
        //
        //     var type = 1;
        //     var ack = $('#service-param-ms-ack').val();
        //     var dest_id = $('#service-param-ms-dest-id').val();
        //     var service_type = 15;
        //     var data = [];
        //
        //     var store_id = $('#service-param-ms-sid').val();
        //
        //     var fun = $('#service-param-ms-function').val();
        //
        //     if(fun == "Format")
        //         if (confirm('Are you sure you want to format the sd?')) {
        //             var service_subtype = 15;
        //         } else {
        //             return 0;
        //         }
        //     } else if(fun == "File_system") {
        //         var action = $('#service-param-ms-action').val();
        //
        //         if(action == "Report") {
        //
        //             var fn = $('#service-param-service-ms-iter').val();
        //
        //             var service_subtype = 12;
        //             data[0] = store_id;
        //
        //             data[1] =  0x000000FF & fn;
        //             data[2] =  0x000000FF & (fn >> 8);
        //             data[3] =  0x000000FF & (fn >> 16);
        //             data[4] =  0x000000FF & (fn >> 24);
        //
        //         } else if(action == "Uplink") {
        //             continue;
        //         } else if(action == "Delete") {
        //
        //             var service_subtype = 11;
        //             data[0] = store_id;
        //
        //             data[1] = 0;
        //
        //             data[2] = 0;
        //             data[3] = 0;
        //             data[4] = 0;
        //             data[5] = 0;
        //         }
        //
        //     } else if(fun == "Enable") {
        //       continue;
        //     }

        //}
        else if (selected_value == "Power") {
            dev_id = $('#service-param-dev-id').val();
            type = 1;
            ack = $('#service-param-power-ack').val();

            service_type = 8;
            service_subtype = 1;
            dest_id = $('#service-param-power-dest_id').val();

            if (dev_id == 1) {
                app_id = 2;
            } else if (dev_id == 2) {
                app_id = 2;
            } else if (dev_id == 3) {
                app_id = 2;
            } else if (dev_id == 4) {
                app_id = 2;
            } else if (dev_id == 5) {
                app_id = 1;
            } else if (dev_id == 6) {
                app_id = 2;
            } else if (dev_id == 7) {
                app_id = 3;
            } else if (dev_id == 8) {
                app_id = 1;
            } else if (dev_id == 9) {
                app_id = 3;
            } else if (dev_id == 10) {
                app_id = 3;
            } else if (dev_id == 11) {
                app_id = 3;
            } else if (dev_id == 12) {
                app_id = 3;
            } else if (dev_id == 13) {
                app_id = 3;
            } else if (dev_id == 14) {
                app_id = 3;
            } else if (dev_id == 15) {
                app_id = 3;
            }

            var fun_id = $('#service-param-function').val();
            data = [fun_id, dev_id];
        } else if (selected_value == "Test") {
            app_id = $('#service-param-test-app_id').val();
            type = 1;
            ack = 0;

            service_type = 17;
            service_subtype = 1;
            dest_id = $('#service-param-test-dest_id').val();
            data = [];
        } else if (selected_value == "Time") {
            // TODO: Is app_id needed in time service?
            //app_id = $('#service-param-time-app_id').val();
            app_id = 1;
            type = 1;
            ack = 0;

            service_type = 17;
            service_subtype = 1;
            dest_id = $('#service-param-time-dest_id').val();

            selected_action = $('#service-param-time-report').find("option:selected").val();

            if (selected_action == 'manual') {
                var datetime = datepicker.data("DateTimePicker").date();
                data = [datetime.utc().format().toString()];
            } else if (selected_action == 'auto') {
                data = [moment().utc().format().toString()];
            } else {
                data = [];
            }
        } else if (selected_value == "ADCS TLE update") {
            // TODO: Is app_id needed in time service?
            //app_id = $('#service-param-time-app_id').val();
            app_id = 7;
            type = 0;
            ack = 0;

            service_type = 3;
            service_subtype = 23;
            dest_id = 3;

            data = [];
            ascii_to_dec($('#service-param-service-tle').val().split(''), data);
            data.unshift(6);
            //number of TLE chanacters
            if (data.length != 137) {
                alert("TLE shouldnt be: " + data.length);
                return 0;
            }
        }

        if (flag) {
            request = encode_service(type, app_id, service_type, service_subtype, dest_id, ack, data, seq_count);
            query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
        } else {
            alert('Please fill ' + missing);
        }
    });

    $("#comms-tx-on").click(function() {
        request = encode_comms_tx_rf(1);
        query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
    });

    $("#comms-tx-off").click(function() {
        request = encode_comms_tx_rf(0);
        query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
    });

    $("#time-radio").change(function() {
        // If checkbox not checked already
        if ($('input[name=power-radio]').prop('checked') === true) {
            var elem = document.getElementById('subservice-params-time');
            var elem2 = document.getElementById('subservice-params-power');
            elem.style.display = "block";
            elem2.style.display = "none";
            $('input[name=power-radio]').prop('checked', false);
            // TODO: Uncheck every other radio
        }
    });

    $(':file').change(function() {
        // var file = this.files[0];
        // var name = file.name;
        // var size = file.size;
        // var type = file.type;
        //Your validation
    });

    $('#upload-btn').click(function() {
        var formData = new FormData($('form')[0]);
        $.ajax({
            url: '/raw', //Server script to process data
            type: 'POST',
            xhr: function() { // Custom XMLHttpRequest
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) { // Check if upload property exists
                    myXhr.upload.addEventListener('progress', progressHandlingFunction, false); // For handling the progress of the upload
                }
                return myXhr;
            },
            //Ajax events
            // beforeSend: beforeSendHandler,
            // success: completeHandler,
            // error: errorHandler,
            // Form data
            data: formData.get('file'),
            //Options to tell jQuery not to process data or worry about content-type.
            cache: false,
            contentType: false,
            processData: false
        });
    });


    //  $("#fileinput").click(function(){
    //     input = document.getElementById('fileinput');
    //
    //     file = input.files[0];
    //     var reader = new FileReader();
    //     reader.onload = function(){
    //         var binaryString = this.result;
    //         $.ajax({
    //            url: '/raw',
    //            type: 'POST',
    //            contentType: 'application/octet-stream',
    //            data: binaryString,
    //            processData: false
    //         });
    //       };
    //     data = reader.readAsBinaryString(file);
    //
    //  });

    $("#send-cmd").click(function() {
        if ($("#command-btn:first-child").text() == 'Test Service') {
            request = encode_test_service();
        } else {
            alert('Invalid command');
            request = false;
        }
        query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
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

    $("#mode-switch li").click(function() {
        var mode = $(this).attr("data-value");
        display_control_view(mode);
    });

});

function display_service(selection) {
    var services = {
        'custom-select': 'service-param-custom',
        'power-select': 'service-param-power',
        'test-select': 'service-param-test',
        'time-select': 'service-param-time',
        'tle-select': 'service-param-tle',
        'ms-select': 'service-param-mass-storage',
        'comms-select': 'service-param-comms',
        'hk-select': 'service-param-housekeeping'
    };
    var keys = [];
    for (var key in services) {
        var elem = document.getElementById(services[key]);
        var service_param_panel = document.getElementById('service-param-panel');
        var service_select = document.getElementById(key);
        if (key == selection) {
            elem.style.display = "block";
            service_param_panel.style.backgroundColor = '#f8f8f8';
        } else {
            elem.style.display = "none";
            service_select.classList.remove('active');
        }
    }
}

function ascii_to_dec(inc, out) {
    for (var i = 0; i < inc.length; i++) {
        out[i] = inc[i].charCodeAt(0);
    }
}

function encode_service(type, app_id, service_type, service_subtype, dest_id, ack, data, seq_count) {
    var DataFieldHeader = {};
    DataFieldHeader.CCSDSSecondaryHeaderFlag = '0';
    DataFieldHeader.TCPacketPUSVersionNumber = '1';
    DataFieldHeader.Ack = ack;
    DataFieldHeader.ServiceType = service_type;
    DataFieldHeader.ServiceSubType = service_subtype;
    DataFieldHeader.SourceID = dest_id;
    DataFieldHeader.Spare = '0';

    var PacketID = {};
    PacketID.VersionNumber = '0';
    PacketID.Type = type;
    PacketID.DataFieldHeaderFlag = '1';
    PacketID.ApplicationProcessID = app_id;

    var PacketSequenceControl = {};
    PacketSequenceControl.SequenceFlags = '3';


    if (typeof seq_count != "undefined") {
        PacketSequenceControl.SequenceCount = seq_count;
    }

    var PacketDataField = {};
    PacketDataField.DataFieldHeader = DataFieldHeader;
    if (data) {
        PacketDataField.ApplicationData = data;
    } else {
        PacketDataField.ApplicationData = '';
    }
    PacketDataField.Spare = '0';
    PacketDataField.PacketErrorControl = '5';

    var PacketHeader = {};
    PacketHeader.PacketID = PacketID;
    PacketHeader.PacketSequenceControl = PacketSequenceControl;
    PacketHeader.PacketLength = '66';

    var TestServicePacket = {};
    TestServicePacket.PacketHeader = PacketHeader;
    TestServicePacket.PacketDataField = PacketDataField;

    var ecss_cmd = {};
    ecss_cmd.ecss_cmd = TestServicePacket;
    ecss_cmd.backend = backend;

    console.log(JSON.stringify(ecss_cmd));
    var json_packet = JSON.stringify(ecss_cmd);
    return json_packet;
}

function encode_comms_tx_rf(status) {
    var response = {};
    var custom_cmd = {};
    var comms_tx_rf = {};
    if (status) {
        custom_cmd.comms_tx_rf = 'comms_on';
    } else {
        custom_cmd.comms_tx_rf = 'comms_off';
    }
    response.custom_cmd = custom_cmd;
    console.log(JSON.stringify(response));
    var json_packet = JSON.stringify(response);
    return json_packet;
}

function encode_backend_mode(mode) {
    var response = {};
    var custom_cmd = {};
    var backend = {};
    if (mode == "gnuradio") {
        custom_cmd.backend = 'gnuradio';
    } else if (mode == "serial") {
        custom_cmd.backend = 'serial';
    }
    response.custom_cmd = custom_cmd;
    console.log(JSON.stringify(response));
    var json_packet = JSON.stringify(response);
    return json_packet;
}

function print_command_response(data) {
    var response_panel = $('#response-panel-body ul');
    var data_type;
    if (data.id == 1) {
        data_type = 'cmd';
        log_data = data.log_message;
    } else if (data.id == 2) {
        data_type = 'ecss';
        log_data = data.log_message;
    } else {
        data_type = 'other';
        log_data = data.log_message;
    }
    response_panel.append('<li class="' + apply_log_filter(data_type) + '"' + ' data-type="' + data_type + '">[' + moment().format('DD-MM-YYYY HH:mm:ss').toString() + '] ' + log_data + '</li>');
    response_panel.scrollTop = response_panel.scrollHeight;
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

function query_control_backend(data, post_mode, url, content_type, data_type, process_data) {
    $.ajax({
        type: post_mode,
        url: url,
        contentType: content_type,
        dataType: data_type,
        data: data,
        processData: process_data,
        success: function(data) {
            print_command_response(data);
        },
        error: function(data) {}
    });
}

function display_control_view(mode) {
    if (mode == 'Network') {
        // Disable Upsat Command and Control
        $('#cnc_mode').css('display', 'none');
        $('#network_mode').css('display', 'block');
    } else if (mode == 'Stand-Alone') {
        // Enable Upsat Command and Control
        $('#cnc_mode').css('display', 'block');
        $('#network_mode').css('display', 'none');
    }
}

function init() {
    // Various variable definition
    var app_id, type, ack, service_type, service_subtype, dest_id, data, seq_count;

    //mode = $("#mode-switch li").attr("data-value");
    mode = Cookies.get('mode');
    display_control_view(mode);

    // Set initial back-end mode
    backend = 'gnuradio';
    request = encode_backend_mode(backend);
    query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);

    // Setup the periodic packet polling
    setInterval(function() {
        query_control_backend({}, 'POST', '/control_rx', "application/json; charset=utf-8", "json", true);
    }, 10000);

    // Setup the datetimepicker
    datepicker = $('#datetimepicker1').datetimepicker({
        format: 'DD-MM-YYYY HH:mm:ss',
    });
}
