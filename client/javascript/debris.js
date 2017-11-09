var map;
var imageMap;

var vectorLayer;
var select;
var vectorSource = new ol.source.Vector({});
var selectedFeatures;
var selectedFeature;
var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');

var vectorLayerImages;
var vectorSourceImages = new ol.source.Vector({});
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

function paintImages(result) {
    var images = result['results'];
    var coords = [];
    var town = getTownId();
    console.log("Town id: " + town);
    images.forEach(function(element) {
        var point = new ol.geom.Point([element['lon'], element['lat']]);
        if(element['town_id'] == town){
            coords.push([element['lon'], element['lat']]);
        }
        var feature = new ol.Feature({
                geometry: point
        });
        feature.setStyle(townStyle(element['town_id']))
        vectorSourceImages.addFeature(feature);
    }); 
    var center = calculateCentroid(coords);
    console.log("Size of element: " + coords.length);
    
    $("#number-images").html("<h1>" + coords.length + "</h1>");
    imageMap.getView().setCenter(center);
    map.getView().setCenter(center);
}


$(document).ready(function(){
    
    vectorLayer = new ol.layer.Vector({
        source: vectorSource
    });
    map = new ol.Map({
        overlays: [overlay],
        target: document.getElementById('map'),
        view: getView(),
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
    retrieveData(SERVER_URL + "/debris/", "GET", paintDebris);



    var urlCall = SERVER_URL + "/samples/list/" + getTownId() + "/?limit=10000";
    console.log(urlCall);
    retrieveData(urlCall, "GET", function(result){
       
        console.log(result['results']);
        var damage = 0;
        var noDamage = 0;

        result['results'].forEach(function(element){
            if(element['label']['name'] == 'Presente'){
                damage++;
            } else if(element['label']['name'] == 'Ausente'){
                noDamage++;
            }
        });
        $("#number-damaged").html("<h1>" + damage + "</h1>");
        $("#number-no-damaged").html("<h1>" + noDamage + "</h1>");

    });




    vectorLayerImages = new ol.layer.Vector({
        source: vectorSourceImages
    });
    imageMap = new ol.Map({
        target: document.getElementById('image-map'),
        view: getView(),
        layers: [
            new ol.layer.Tile({
            source: new ol.source.OSM()
            }),
            vectorLayerImages
        ]
    });
    retrieveData(SERVER_URL + "/allimages/?limit=10000", "GET", paintImages);
});