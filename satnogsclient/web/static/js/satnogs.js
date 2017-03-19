$(document).ready(function() {
    //Socket.io connection for backend configuration
    var config_socket = io.connect('http://' + document.domain + ':' + location.port + '/config', {
        rememberTransport: false,
        'reconnect': true,
        'reconnection delay': 500,
        'max reconnection attempts': 10
    });

    config_socket.on('connect', function() {
        $('#backend-status').addClass('online-circle').removeClass('offline-circle').attr('title', 'Backend Online');
        console.log('Frontend connected to backend!');
        current_mode = Cookies.get('mode');
        request = encode_mode_switch(current_mode);
        config_socket.emit('mode_change', request);
    });

    config_socket.on('connect_error', function() {
        $('#backend-status').removeClass('online-circle').addClass('offline-circle').attr('title', 'Backend Offline');
        console.log('Frontend cannot connect to backend!');
    });

    config_socket.on('backend_msg', function(data) {
        console.log('Received from backend: ' + JSON.stringify(data));
    });

    init_view();

    $("#mode-switch li").click(function() {
        var selected = $(this).attr("data-value");
        Cookies.set('mode', selected);
        // Inform backend about the mode change
        request = encode_mode_switch(selected);
        config_socket.emit('mode_change', request);

        $('#mode-switch :button').contents()[0].nodeValue = selected + " Mode ";
        document.cookie = selected;
        var listItems = $('#mode-switch li');
        for (var i = 0; i < listItems.length; i++) {
            var currentItem = listItems[i];
            if (currentItem.getAttribute('data-value') == selected) {
                currentItem.style.display = "none";
            } else {
                currentItem.style.display = "block";
            }
        }
    });

    function init_view() {
        if (Cookies.get('mode')) {
            current_mode = Cookies.get('mode');
            $('#mode-switch :button').contents()[0].nodeValue = current_mode + " Mode ";
            var listItems = $('#mode-switch li');
            for (var i = 0; i < listItems.length; i++) {
                var currentItem = listItems[i];
                if (currentItem.getAttribute('data-value') == current_mode) {
                    currentItem.style.display = "none";
                } else {
                    currentItem.style.display = "block";
                }
            }
        } else if (Cookies.get('mode') === null || typeof mode === 'undefined') {
            //TODO: Fix hardcoded initialization
            current_mode = "Network";
            Cookies.set('mode', current_mode);
        }
        // Send a request to backend in order to configure mode.
        request = encode_mode_switch(current_mode);
        config_socket.emit('mode_change', request);
    }

    function encode_mode_switch(mode) {
        var response = {};
        var custom_cmd = {};
        var comms_tx_rf = {};
        if (mode == "Stand-Alone") {
            custom_cmd.mode = 'cmd_ctrl';
        } else if (mode == "Network") {
            custom_cmd.mode = 'network';
        }
        response.custom_cmd = custom_cmd;
        var json_packet = JSON.stringify(response);
        return json_packet;
    }

});
