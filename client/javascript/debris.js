
function retrieveData(urlCall) {
    $.ajax({
        type: 'GET',
        url: urlCall, 
        success: function(result){
            console.log(result);
            result.forEach(function(element) {
                var point = new ol.geom.Point([element['lon'], element['lat']]);
                var feature = new ol.Feature({
                        name: "Thing",
                        address: element['address'],
                        geometry: point
                });
                vectorSource.addFeature(feature);
            }); 
        },
        beforeSend : function(req) {
            req.setRequestHeader('Authorization',  'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}
var map;

var vectorLayer;
var select;
var vectorSource = new ol.source.Vector({});

var selectedFeatures;
var selectedFeature;

var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');

closer.onclick = function() {
  overlay.setPosition(undefined);
  closer.blur();
  return false;
};


/**
 * Create an overlay to anchor the popup to the map.
 */
var overlay = new ol.Overlay(/** @type {olx.OverlayOptions} */ ({
    element: container,
    autoPan: true,
    autoPanAnimation: {
    duration: 250
  }
}));



$(document).ready(function(){
    
    var center = [-94.83657579261286, 16.47216369265396];

    vectorLayer = new ol.layer.Vector({
        source: vectorSource
    });

    map = new ol.Map({
        overlays: [overlay],
        target: document.getElementById('map'),
        view: new ol.View({
            projection: 'EPSG:4326',
            center: center,
            zoom: 16,
            minZoom: 14,
            maxZoom: 19
        }),
        layers: [
            new ol.layer.Tile({
            source: new ol.source.OSM()
            }),
            vectorLayer
        ]
    });
    select = new ol.interaction.Select({
      layers: [vectorLayer]
    });

    map.addInteraction(select);
    selectedFeatures = select.getFeatures();


    map.on('click', function(event) { 
        if(selectedFeature != null) {
            var coordinate = event.coordinate;
            content.innerHTML = '<p>' + selectedFeature.get('address') + '</p>';
            overlay.setPosition(coordinate);
        }
    });

    selectedFeatures.on('add', function(event) {
        selectedFeature = event.target.item(0);
    });
    selectedFeatures.on('remove', function(event) {
        selectedFeature = null;
    });


    
    retrieveData("http://localhost:8000/debris/");

    
});