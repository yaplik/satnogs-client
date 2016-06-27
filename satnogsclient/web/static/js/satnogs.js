$(document).ready(function() {

init_view();

$("#mode-switch li").click(function() {
      var selected = $(this).attr("data-value");
      Cookies.set('mode', selected);

      // Inform backend about the mode change
      request = encode_mode_switch(selected);
      query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);

      $('#mode-switch :button').contents()[0].nodeValue = selected + " Mode ";
      document.cookie= selected;
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
   }
   else if (Cookies.get('mode') == null) {
     //TODO: Fix hardcoded initialization
     default_mode = "Network";
     Cookies.set('mode', default_mode);
     // Send an initial request to backend in order to configure mode.
     request = encode_mode_switch(default_mode);
     query_control_backend(request, 'POST', '/command', "application/json; charset=utf-8", "json", true);
   }
  }

  function encode_mode_switch(mode) {
    var response = new Object();
    var custom_cmd = new Object();
    var comms_tx_rf = new Object();
    if (mode == "Stand-Alone") {
        custom_cmd.mode = 'cmd_ctrl';
    }
    else if (mode == "Network") {
        custom_cmd.mode = 'network';
    }
    response.custom_cmd = custom_cmd;
    console.log(JSON.stringify(response));
    var json_packet = JSON.stringify(response);
    return json_packet;
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
        error: function(data) {
        }
    });
  }

});
