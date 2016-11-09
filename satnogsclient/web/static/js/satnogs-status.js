/*jshint multistr: true */

function AnimateRotate(degrees) {
    var $elem = $('#current-pass-arrow');
    $({
        deg: degrees
    }).animate({
        deg: degrees
    }, {
        duration: 2000,
        step: function(now) {
            $elem.css({
                transform: 'rotate(' + now + 'deg)'
            });
        }
    });
}

function initMap(lat, lng) {
    var latf = parseFloat(lat);
    var lngf = parseFloat(lng);
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 1,
        center: new google.maps.LatLng(latf, lngf)
    });

    var marker = new google.maps.Marker({
        position: new google.maps.LatLng(latf, lngf),
        map: map,
        title: 'Hello World!'
    });

    map.setZoom(1);
    return map;
}

function update_status_ui(data, param) {
    update_observations(data, param);
}

function update_observations(data, param) {
    var json_data = data;
    var current_obs = json_data.observation.current;
    var scheduled_obs = json_data.observation.scheduled;
    var tle1_current = current_obs.tle1.split(' ');
    var tle2_current = current_obs.tle2.split(' ');

    //Update current observation
    if (current_obs.azimuth === "NA" && current_obs.altitude === "NA") {
        document.getElementById("azimuth").innerHTML = current_obs.azimuth;
        document.getElementById("elevation").innerHTML = current_obs.altitude;
    } else {
        document.getElementById("azimuth").innerHTML = current_obs.azimuth + " &deg;";
        document.getElementById("elevation").innerHTML = current_obs.altitude + " &deg;";
        // TODO: Fix map and marker update. Lat/Lng values should be valid
        param.setCenter(new google.maps.LatLng(current_obs.azimuth, current_obs.altitude));
        // Polar graph update
        AnimateRotate(parseFloat(current_obs.azimuth));
    }
    if (current_obs.frequency === "NA") {
        document.getElementById("freq").innerHTML = current_obs.frequency;
    } else {
        document.getElementById("freq").innerHTML = current_obs.frequency + " MHz";
    }

    document.getElementById("name").innerHTML = current_obs.tle0;
    document.getElementById("obs-id").innerHTML = tle2_current[1];
    document.getElementById("current-tle1").innerHTML = current_obs.tle1;
    document.getElementById("current-tle2").innerHTML = current_obs.tle2;

    //Update scheduled observations
    var tr;
    if (scheduled_obs.length > 0) {
        $('#scheduled-observation-table tr:not(:first)').remove();
        for (i = 0; i < scheduled_obs.length; i++) {
            var freq = parseFloat(scheduled_obs[i].frequency) / 10e5;
            if (isNaN(freq)) {
                freq = 'NA';
            } else {
                freq = freq.toFixed(2) + ' MHz';
            }
            tr = "<tr> \
                    <td>" + scheduled_obs[i].tle0 + "</td> \
                    <td>" + scheduled_obs[i].start + "</td> \
                    <td>" + scheduled_obs[i].end + "</td> \
                    <td>" + freq + "</td> \
                  </tr>";
            $('#scheduled-observation-table').append(tr);
        }
    } else {
        $('#scheduled-observation-table tr:not(:first)').remove();
        tr = "<tr><td colspan='4'>No observations scheduled</td></tr>";
        $('#scheduled-observation-table').append(tr);
    }
}

function query_status_info(JSONData, localMode, url, param) {
    var localJSONData = JSONData;
    var postMode = localMode;

    $.ajax({
        type: postMode,
        url: url,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        data: JSONData,
        success: function(data) {
            update_status_ui(data, param);
        }
    });
}

// Initialize status page
$(document).ready(function() {
    document.getElementById("azimuth").innerHTML = "NA";
    document.getElementById("elevation").innerHTML = "NA";
    document.getElementById("freq").innerHTML = "NA";
    document.getElementById("name").innerHTML = "NA";
    document.getElementById("obs-id").innerHTML = "NA";
    document.getElementById("rising").innerHTML = "NA";
    document.getElementById("setting").innerHTML = "NA";
    document.getElementById("max-alt").innerHTML = "NA";
    document.getElementById("demod").innerHTML = "NA";
    document.getElementById("decod").innerHTML = "NA";
    document.getElementById("current-tle1").innerHTML = "NA";
    document.getElementById("current-tle2").innerHTML = "NA";
    document.getElementById("decod").innerHTML = "NA";
    map = initMap(49.496675, -102.65625);

    setInterval(function() {
        query_status_info({}, 'GET', '/update_status', map);
    }, 2000);

});
