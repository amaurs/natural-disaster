var map;
var vectorLayer;
var select;
var vectorSource = new ol.source.Vector({});
var selectedFeatures;
var selectedFeature;
var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');
var overlay = new ol.Overlay(({
    element: container,
    autoPan: true,
    autoPanAnimation: {
    duration: 250
  }
}));

closer.onclick = function() {
  overlay.setPosition(undefined);
  closer.blur();
  return false;
};


function paintDebris(result) {
    result.forEach(function(element) {
        var point = new ol.geom.Point([element['lon'], element['lat']]);
        var feature = new ol.Feature({
                address: element['address'],
                geometry: point
        });
        vectorSource.addFeature(feature);
    }); 
}


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
            zoom: 15,
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
    retrieveData(SERVER_URL + "/debris/", paintDebris);
});