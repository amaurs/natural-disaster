var imageMap;
var town = 3;
var vectorLayerImages;
var vectorSourceImages = new ol.source.Vector({});


function townStyle(town) {
    var style = new ol.style.Style({
        image: new ol.style.Circle({
            radius: 3,
            fill: new ol.style.Fill({
                color: town==3?'blue':(town==1?'red':'green')
            })
        })
    });
    return style;
}

function retrieveDataImages(urlCall) {
    $.ajax({
        type: 'GET',
        url: urlCall, 
        success: function(result){
            var images = result['results'];
            var coords = [];
            console.log(images);
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
            imageMap.getView().setCenter(center);
        },
        beforeSend : function(req) {
            req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}

$(document).ready(function(){
    var center = [-94.83657579261286, 16.47216369265396];
    vectorLayerImages = new ol.layer.Vector({
        source: vectorSourceImages
    });
    imageMap = new ol.Map({
        target: document.getElementById('image-map'),
        view: new ol.View({
            projection: 'EPSG:4326',
            center: center,
            zoom: 15,
            minZoom: 10,
            maxZoom: 19
        }),
        layers: [
            new ol.layer.Tile({
            source: new ol.source.OSM()
            }),
            vectorLayerImages
        ]
    });
    retrieveDataImages(SERVER_URL + "/allimages/?limit=10000");
});