/**
 * Created by boliangzhang on 11/15/15.
 */

$(document).ready(function() {
    /*
     Login
     */
    $('#login').submit(function (event) {
        // This will prevent the browser from submitting the form, allowing us to handle the file upload using AJAX instead.
        event.preventDefault();

        var dev_code = $('#dev_code').val();

        var formData = new FormData();

        formData.append('dev_code', dev_code);

        var xhr = new XMLHttpRequest();

        // Open the connection.
        xhr.open('POST', '/elisa_ie', true);

        // Set up a handler for when the request finishes.
        xhr.onload = function () {
            if (xhr.status == 200) {
                document.open();
                document.write(xhr.responseText);
                document.close();
            }
            else {
                alert("incorrect dev code");
            }
        };

        xhr.send(formData);
    });
});