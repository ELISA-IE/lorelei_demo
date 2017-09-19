/**
 * Author: Ying Lin
 * Date: Aug 31, 2017
 */
var DATA_SOURCE = '/data';
var loading_div = $('#loading');

mapboxgl.accessToken = 'pk.eyJ1IjoibGltdGVuZyIsImEiOiJjajJjcGdzNjUwM2NkMndvNzBpeTBrZjFwIn0.9YDJZ3qB_VuNHF3L-ni6PQ';
var map = new mapboxgl.Map({
    minZoom: 2,
    maxZoom: 15,
    container: 'map-wrapper',
    style: 'mapbox://styles/mapbox/dark-v9'
});


function initialize_map() {
    // Load icons
    map.loadImage('/static/images/heatmap/icon_food.png', function (error, image) {
        if (error) throw error;
        map.addImage('food', image);
    });
    map.loadImage('/static/images/heatmap/icon_water.png', function (error, image) {
        if (error) throw error;
        map.addImage('water', image);
    });
    map.loadImage('/static/images/heatmap/icon_medical.png', function (error, image) {
        if (error) throw error;
        map.addImage('medical', image);
    });
    map.loadImage('/static/images/heatmap/icon_violence.png', function (error, image) {
        if (error) throw error;
        map.addImage('violence', image);
    });
    map.loadImage('/static/images/heatmap/icon_energy.png', function (error, image) {
        if (error) throw error;
        map.addImage('energy', image);
    });
    map.loadImage('/static/images/heatmap/icon_infrastructure.png', function (error, image) {
        if (error) throw error;
        map.addImage('infrastructure', image);
    });
    map.loadImage('/static/images/heatmap/icon_rescue.png', function (error, image) {
        if (error) throw error;
        map.addImage('rescue', image);
    });
    map.loadImage('/static/images/heatmap/icon_shelter.png', function (error, image) {
        if (error) throw error;
        map.addImage('shelter', image);
    });
    map.loadImage('/static/images/heatmap/icon_evacuation.png', function (error, image) {
        if (error) throw error;
        map.addImage('evacuation', image);
    });
    map.loadImage('/static/images/heatmap/icon_crime.png', function (error, image) {
        if (error) throw error;
        map.addImage('crime', image);
    });
    // map.addLayer({
    //     'id': '3d-buildings',
    //     'source': 'composite',
    //     'source-layer': 'building',
    //     'filter': ['==', 'extrude', 'true'],
    //     'type': 'fill-extrusion',
    //     'minzoom': 15,
    //     'paint': {
    //         'fill-extrusion-color': '#aaa',
    //         'fill-extrusion-height': {
    //             'type': 'identity',
    //             'property': 'height'
    //         },
    //         'fill-extrusion-base': {
    //             'type': 'identity',
    //             'property': 'min_height'
    //         },
    //         'fill-extrusion-opacity': .6
    //     }
    // });

    $.getJSON('/elisa_ie/heatmap/data', function (data) {
        // Add data source
        map.addSource('data', {
            type: 'geojson',
            data: data
        });

        // Add language layer
        map.addLayer({
            id: 'languages',
            type: 'circle',
            source: 'data',
            paint: {
                'circle-color': {
                    property: 'language',
                    type: 'categorical',
                    stops: [
                        ['Somali', 'rgb(178, 122, 10)'],
                        ['Oromo', 'rgb(239, 183, 70)'],
                        ['Tigrinya', 'rgb(73, 165, 165)'],
                        ['Amharic', 'rgb(42, 144, 144)'],
                        ['English', 'rgb(226, 115, 23)'],
                        ['Hausa', 'rgb(174, 36, 174)'],
                        ['Georgian', 'rgb(130, 230, 48)'],
                        ['Farsi', 'rgb(80, 177, 0)'],
                        ['Russian', 'rgb(235, 89, 133)'],
                        ['Ukrainian', 'rgb(228, 0, 69)'],
                        ['Turkish', 'rgb(71, 188, 162)'],
                        ['Kurdish', 'rgb(0, 164, 127)'],
                        ['Nepali', 'rgb(103, 168, 226)'],
                        ['Bengali', 'rgb(53, 142, 222)'],
                        ['Urdu', 'rgb(12, 122, 221)'],
                        ['Lao', 'rgb(246, 244, 1)'],
                        ['Thai', 'rgb(236, 235, 70)'],
                        ['Khmer', 'rgb(255, 226, 8)'],
                        ['Vietnamese', 'rgb(215, 188, 0)'],
                        ['Indonesian', 'rgb(196, 0, 49)'],
                        ['Japanese', 'rgb(233, 72, 112)'],
                    ]

                },
                'circle-radius': {
                    stops: [[1, 3], [15, 10]]
                },
                'circle-opacity': {
                    stops: [[1, .03], [18, .5]]
                },
                'circle-blur': 0
            }
        });

        // Add icon layer
        map.addLayer({
            id: 'icons',
            type: 'symbol',
            source: 'data',
            layout: {
                'icon-image': {
                    property: 'topic',
                    type: 'categorical',
                    stops: [
                        ['Food Supply', 'food'],
                        ['Water Supply', 'water'],
                        ['Medical Assistance', 'medical'],
                        ['Terrorism or other Extreme Violence', 'violence'],
                        ['Utilities, Energy, or Sanitation', 'energy'],
                        ['Evacuation', 'evacuation'],
                        ['Shelter', 'shelter'],
                        ['Search and Rescue', 'rescue'],
                        ['Civil Unrest or Wide-spread Crime', 'crime'],
                        ['Infrastructure', 'infrastructure']
                    ]
                },
                'icon-size': {stops: [[1, .2], [15, .5]]},
                'icon-padding': {stops: [[1, 30], [15, 2]]},
                // 'icon-opacity': {stops: [[1, .5], [3, 1]]}
            }
        });

        // map.addLayer({
        //     id: 'labels',
        //     type: 'symbol',
        //     source: 'data',
        //     'layout': {
        //         'text-field': '{language}',
        //         'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
        //         'text-size': 12,
        //         'text-ignore-placement': true
        //     },
        //     'paint': {
        //         'text-color': 'rgba(255,255,255,.5)'
        //     }
        // });


        map.on('click', 'icons', function (e) {
            $('#popup').css('display', 'flex').fadeIn(200);
            $('#popup-text').html(e.features[0].properties.sentence);
            $('#popup-text-language').html(e.features[0].properties.language);
            $('#popup-text-title').html(e.features[0].properties.location);

        });

        // Change the cursor to a pointer when the mouse is over the places layer.
        map.on('mouseenter', 'icons', function () {
            map.getCanvas().style.cursor = 'pointer';
        });

        // Change it back to a pointer when it leaves.
        map.on('mouseleave', 'icons', function () {
            map.getCanvas().style.cursor = '';
        });

        setTimeout(function () {
            loading_div.fadeOut(200);
        }, 500);
    });
}
setTimeout(function () {
    initialize_map();
}, 2000);


function reset_maps() {
    map.off('click', 'icons');
    map.off('mouseenter', 'icons');
    map.off('mouseleave', 'icons');
    map.removeLayer('icons');

    map.removeLayer('languages');

    map.removeImage('food');
    map.removeImage('water');
    map.removeImage('medical');
    map.removeImage('violence');
    map.removeImage('energy');
    map.removeImage('infrastructure');
    map.removeImage('rescue');
    map.removeImage('shelter');
    map.removeImage('evacuation');
    map.removeImage('crime');

    map.removeSource('data');

    map = new mapboxgl.Map({
        minZoom: 2,
        maxZoom: 18,
        container: 'map-wrapper',
        style: 'mapbox://styles/mapbox/dark-v9'
    });
    $('#map-topic-select').val('all');
    $('#map-language-select').val('all');
}

// close popup
$('#popup-close').click(function () {
    $('#popup').fadeOut(200);
});

// switch style
$('.map-style-toggle').click(function () {
    loading_div.fadeIn(100);
    var button = $(this);
    var style = button.attr('value');
    // ui style
    $('#map-control')
        .removeClass('dark')
        .removeClass('light')
        .removeClass('streets')
        .removeClass('satellite')
        .addClass(style);
    // map style
    reset_maps();
    map.setStyle('mapbox://styles/mapbox/' + style + '-v9');
    setTimeout(function () {
        initialize_map();
    }, 2000);
    if (style === 'light' || style === 'streets') {
        $('#map-topic-list').addClass('light');
    } else {
        $('#map-topic-list').removeClass('light');
    }
});

function filter(layer, key, value) {
    if (value === 'all') {
        map.setFilter(layer, undefined);
    } else {
        map.setFilter(layer, ['==', key, value]);
    }
}

$('#map-topic-select,#map-language-select').change(function () {
    var topic_val = $('#map-topic-select').val();
    var lang_val = $('#map-language-select').val();
    map.setFilter('icons', undefined);
    map.setFilter('languages', undefined);
    if (topic_val !== 'all' || lang_val !== 'all') {
        map.setFilter('icons', undefined);
        map.setFilter('languages', undefined);

        var filters = ['all'];
        if (topic_val !== 'all') {
            filters.push(['==', 'topic', topic_val]);
        }
        if (lang_val !== 'all') {
            filters.push(['==', 'language', lang_val]);
        }
        map.setFilter('icons', filters);
        map.setFilter('languages', filters);
    }
});