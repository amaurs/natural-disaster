var map;
var imageMap;
var vectorLayer;
var select;
var vectorSource = new ol.source.Vector({});
var selectedFeatures;
var selectedFeature;
var vectorLayerImages;
var vectorSourceImages = new ol.source.Vector({});

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
    
    $("#number-images").html(coords.length);
    imageMap.getView().setCenter(center);
}


$(document).ready(function(){
    
    vectorLayer = new ol.layer.Vector({
        source: vectorSource
    });
    $("#title").text(getTownName());


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
        $("#number-damaged").html(damage);
        $("#number-no-damaged").html(noDamage);

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