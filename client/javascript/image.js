
var map;
var town = 3;
var vectorLayer;
var vectorSource = new ol.source.Vector({});

function calculateCentroid(coords) {
  let longitude = 0;
  let latitude = 0;

  for (let i = 0; i < coords.length; i++) {
    longitude += coords[i][0];
    latitude += coords[i][1];
  }

  return [longitude / coords.length, latitude / coords.length];
}

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

function retrieveData(urlCall) {
    $.ajax({
        type: 'GET',
        url: urlCall, 
        success: function(result){
            images = result['results'];
            coords = [];
            images.forEach(function(element) {
                var point = new ol.geom.Point([element['lon'], element['lat']]);
                if(element['town_id'] == town){
                    coords.push([element['lon'], element['lat']]);
                }
                var feature = new ol.Feature({
                        geometry: point
                });
                feature.setStyle(townStyle(element['town_id']))
                vectorSource.addFeature(feature);
            }); 
            var center = calculateCentroid(coords);
            map.getView().setCenter(center);
        },
        beforeSend : function(req) {
            req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}

$(document).ready(function(){
    var center = [-94.83657579261286, 16.47216369265396];
    vectorLayer = new ol.layer.Vector({
        source: vectorSource
    });
    map = new ol.Map({
        target: document.getElementById('map'),
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
            vectorLayer
        ]
    });
    retrieveData("http://localhost:8000/allimages/?limit=10000");
});