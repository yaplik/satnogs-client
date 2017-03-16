$(document).ready(function() {

  init();

});

function init() {

  datetimepicker_start = $('#gs_cnc_start').datetimepicker({
      format: 'DD-MM-YYYY HH:mm:ss',
  });

  datetimepicker_end = $('#gs_cnc_end').datetimepicker({
      format: 'DD-MM-YYYY HH:mm:ss',
  });

}

// var datetime = datepicker_time.data("DateTimePicker").date();
// dateutc = datetime;
//
// if (dateutc.day() === 0) {
//     weekday = 7;
// } else {
//     weekday = dateutc.day();
// }
//
// data.splice(0, 0, weekday);
// data.splice(1, 0, dateutc.date());
// data.splice(2, 0, dateutc.month() + 1); // 7 is delete all mode
// data.splice(3, 0, dateutc.year() - 2000); // pads for keeping same format as delete
// data.splice(4, 0, dateutc.hour());
// data.splice(5, 0, dateutc.minute());
// data.splice(6, 0, dateutc.seconds());
