$(function() {
    $('#config-save-button').on('click', function(e) {
        var table = document.getElementById("config-table");
        var array = {};
        array.configuration = {};
        for (var i = 1, row; row == table.rows[i]; i++) {
            array.configuration[row.cells[0].innerText] = row.cells[1].innerText;
        }
        var json = JSON.stringify(array);
        postJSONData(json, "POST", "/config_update");
    });
});
