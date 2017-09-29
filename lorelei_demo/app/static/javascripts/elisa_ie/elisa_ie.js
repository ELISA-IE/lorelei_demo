/**
 * Created by boliangzhang on 4/24/16.
 */
var seleted_doc_index = 0;
var sample_docs = null;

$(document).ready(function() {
    /*
     Demo Seciton
     This panel handles workflow between name taggers and interface in demo section.
     */

    // language selection button dropdown
    demo_il_dropdown_button();
    detect_click_outside();
    il_button();

    // call demo_il_selection once here
    demo_il_selection();

    //
    // buttons of example demo input documents
    //
    $('.btn-sm').click(function () {
        // global varaibale. track selected example
        var btn_index = $(this).attr('btn_index');
        var demo_input = $('#demo_input');
        if (btn_index == '3') {
            demo_input.prop('disabled', false);
            demo_input.val('enter sentences in incident language...');
            demo_input.prop('defaultValue', 'enter sentences in incident language...');

            seleted_doc_index = btn_index;
            return;
        }

        demo_input.val(sample_docs[parseInt(btn_index)]);
        demo_input.prop('disabled', true);

        seleted_doc_index = btn_index;
    });

    //
    // default input textarea
    //
    $("#demo_input")
        .focus(function () {
            if (this.value === this.defaultValue) {
                this.value = '';
            }
        })
        .blur(function () {
            if (this.value === '') {
                this.value = this.defaultValue;
            }
        });

    //
    // change languages options in demo
    //
    $('#demo_il_selection').change(demo_il_selection);

    //
    // form submit (run ner)
    //
    $('#demo_form').submit(function (event) {
        var demo_result = $('#demo_result');
        demo_result.hide();

        var selected_il = $('#demo_il_selection').find(":selected").val();
        $(".update_heatmap").show();

        // This will prevent the browser from submitting the form, allowing us to handle the file upload using AJAX instead.
        event.preventDefault();

        var demo_button = $('#demo_tag_button');
        demo_button.text('Tagging...');
        demo_button.prop('disabled', true);

        // Create a new FormData object.
        // This is used to construct the key/value pairs which form the data payload for the AJAX request
        var formData = new FormData();

        // Add the file to the request.
        formData.append('demo_input', $('#demo_input').val());
        formData.append('seleted_il', selected_il);
        formData.append('seleted_doc_index', seleted_doc_index);

        var xhr = new XMLHttpRequest();

        // Open the connection.
        xhr.open('POST', '/elisa_ie/run', true);

        // Set up a handler for when the request finishes.
        xhr.onload = function () {
            if (xhr.status === 200) {
                // show ner result visualization
                var response_json = JSON.parse(xhr.responseText);

                var visualization_html = response_json.visualization_html;

                demo_button.text('Submit');
                demo_button.prop('disabled', false);

                $('#demo_result_html').html(visualization_html);

                // add image slider animation
                // image_slider_animation();

                demo_result.show();
            }
        };

        // Send the Data.
        xhr.send(formData);
    });
});


function demo_il_selection () {
    var selected_il = $('#demo_il_selection').find(":selected").val();

    // fetch sample documents from server
    var xhr = new XMLHttpRequest();
    var url = '/elisa_ie/sample_doc/' + selected_il;
    xhr.open('GET', url, false);
    xhr.send( null );
    sample_docs = JSON.parse(xhr.responseText).sample_docs;

    var direction = $('#demo_il_selection').find(":selected").attr('direction');
    var demo_input = $('#demo_input');
    demo_input.val(sample_docs[0]);
    demo_input.prop('disabled', true);

    $('.btn-sm').show();
    $('#tagger_description').show();
    $('#demo_tagger_selection').show();
    $('#demo_instruction').show();

    // hide annotation result
    $('#demo_result').hide();
    $('#demo_result_title').hide();

    // reset selected doc example index to 0
    seleted_doc_index = 0;

    // change input text area direction
    if (direction == 'rtl'){
        $('#demo_input').css({'direction': 'rtl'});
    }
    else{
        $('#demo_input').css({'direction': 'ltr'});
    }
}


function image_slider_animation() {
    // image slider animation
    $('.slider').each(function(i, obj) {
        var div_index = $(this).attr('index');
        var slideCount = $('#slider' + div_index + ' ul li').length;
        var slideWidth = $('#slider' + div_index + ' ul li').width();
        var slideHeight = $('#slider' + div_index + ' ul li').height();
        var sliderUlWidth = slideCount * slideWidth;

        $('#slider' + div_index + '').css({
            width: slideWidth,
            height: slideHeight
        });

        $('#slider' + div_index + ' ul').css({
            width: sliderUlWidth,
            marginLeft: -slideWidth
        });

        $('#slider' + div_index + ' ul li:last-child').prependTo('#slider' + div_index + ' ul');

        function moveLeft() {
            $('#slider' + div_index + ' ul').animate({
                left: +slideWidth
            }, 200, function() {
                $('#slider' + div_index + ' ul li:last-child').prependTo('#slider' + div_index + ' ul');
                $('#slider' + div_index + ' ul').css('left', '');
            });
        };

        function moveRight() {
            $('#slider' + div_index + ' ul').animate({
                left: -slideWidth
            }, 200, function() {
                $('#slider' + div_index + ' ul li:first-child').appendTo('#slider' + div_index + ' ul');
                $('#slider' + div_index + ' ul').css('left', '');
            });
        };

        $('a#ctrl_prev_' + div_index).click(function() {
            moveLeft();
            return false;
        });

        $('a#ctrl_next_' + div_index).click(function() {
            moveRight();
            return false;
        });
    });
}

function expand_select_dropdown(select_id, online_languages){
    var online_languages = JSON.parse(online_languages);
    var demo_il_selection = $('#demo_il_selection');
    var added_language_group = [];

    jQuery.each(online_languages, function(i, val) {
        var language_code = i;
        var language_name = val[0];
        var language_status = val[1];
        var language_group = val[2];
        var direction = val[3];

        // create new option element
        var option = $("<option>", {value: language_code, text: language_name, direction: direction});
        if (added_language_group.includes(language_group)){
            var optgroup = $('#'+select_id+' optgroup[label='+language_group+']');
        }
        else{
            var optgroup = $("<optgroup>", {label: language_group});
            optgroup.appendTo(demo_il_selection);
            added_language_group.push(language_group);
        }

        option.appendTo(optgroup);
    });
}

//
// button dropdown (language selection)
//
var demo_il_panel_open = false;

/* Dropdown button listener */
function demo_il_dropdown_button() {
    $('#demo_il_dropdown_btn').click(function() {
        if (demo_il_panel_open) {
            demo_il_panel_open = false;
            $('#demo_il_panel').hide();
        } else {
            demo_il_panel_open = true;
            $('#demo_il_panel').show();
        }
    });
}


/* Close the demo il panel when clicking outside of the panel */
function detect_click_outside() {
    $('html').click(function() {
        if (demo_il_panel_open) {
            demo_il_panel_open = false;
            $('#demo_il_panel').hide();
        }
    });

    $('#demo_il_panel_wrapper').click(function(event){
        event.stopPropagation();
    });
}

/* Language button listener */
function il_button() {
    $('.demo_il_button').click(function() {
        var value = $(this).attr('value'); // get the language code
        // ADD YOUR CODE HERE
        //......
        $('#demo_il_selection').val(value).trigger('change');

        // close the panel
        demo_il_panel_open = false;
        $('#demo_il_panel').hide();
    })
}
