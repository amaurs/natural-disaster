var width = 4000;
var height = 3000;
var featureWidth = featureHeight = 322;
var extent = [0, 0, width, height];
var source = new ol.source.Vector({wrapX: false});

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
closer.onclick = closePopup;

function closePopup() {
    overlay.setPosition(undefined);
    closer.blur();
    return false;
}


var projection = new ol.proj.Projection({
  code: 'photo-image',
  units: 'pixels',
  extent: extent
});

var raster = new ol.layer.Image();


var polygonFeature = new ol.Feature(
    new ol.geom.Polygon([[[(width - featureWidth) / 2, (height - featureHeight) / 2], 
                          [(width + featureWidth) / 2, (height - featureHeight) / 2],
                          [(width + featureWidth) / 2, (height + featureHeight) / 2], 
                          [(width - featureWidth) / 2, (height + featureHeight) / 2], 
                          [(width - featureWidth) / 2, (height - featureHeight) / 2]]]));

var vectorSource = new ol.source.Vector({features: [polygonFeature]});
var vector = new ol.layer.Vector({
    source: vectorSource
});


var select = new ol.interaction.Select();

var translate = new ol.interaction.Translate({
  features: select.getFeatures()
});

translate.on("translateend", function(event){
    var extent = polygonFeature.getGeometry().getExtent();
    var x = Math.round(extent[0]);
    var y = Math.round(height - (featureHeight + extent[1]));
    var w = featureWidth;
    var h = featureHeight;
    console.log("("+x+","+y+","+w+","+h+")");
    if(x < 0 || x + w >= width || y < 0 || y + h >= height) {
        $("#submit").prop('disabled', true);
    } else {
        $("#submit").prop('disabled', false);
    }
});
var map = new ol.Map({
    overlays: [overlay],
    layers: [raster, vector],
    target: 'map',
    view: new ol.View({
      projection: projection,
      center: ol.extent.getCenter(extent),
      zoom: 2,
      maxZoom: 8
    }),
    interactions: ol.interaction.defaults().extend([select, translate])
});

var global = {};

function getSource(newUrl) {
    var finalUrl = newUrl;
    newSource = new ol.source.ImageStatic({
                        url: finalUrl,
                        projection: projection,
                        imageExtent: extent
                    });
    return newSource;
}
function loadNewImage() {
    source = getSource(global.currentData['results'][global.index]['url']);
    layer = map.getLayers().getArray()[0];
    layer.setSource(source);
}
function makeAjaxCall(urlCall, load) {
    $.ajax({
        type: 'GET',
        url: urlCall, 
        success: function(result){
            global.currentData = result;
            //Needs to be checked, this is clearly a hack.
            if(load) { 
                global.index = 0;
                loadNewImage();
            }
        },
        beforeSend : function(req) {
            req.setRequestHeader('Authorization',  'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function sendInfo(uuid, url, x, y, w, h, label) {
    $.ajax({
        url: "http://localhost:8000/samples/",
        type: "POST",
        data: JSON.stringify({
            "name": uuid + ".jpg",
            "url": "http://localhost:8081/thumb/" + uuid + ".jpg",
            "image": {
                "url": url
            },
            "height": h,
            "width": w,
            "y": y,
            "x": x,
            "label": {
                "name": label
            }
        }),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            console.log("Upload was successful.");
        },
        beforeSend : function(request) {
            request.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        }
    });
}

$(document).ready(function(){
    var data;
    makeAjaxCall("http://localhost:8000/images/", true);
    $("#next").click(function(){
        if (global.currentData) {
            var size = global.currentData['results'].length;
            if(global.index + 1 < size){
                global.index = global.index + 1;
            } else if(global.currentData['next'] != null){
                makeAjaxCall(global.currentData['next'], false);
                global.index = 0;
            } else {
                console.log("Last page.");
            }
            loadNewImage();
        } else {
            makeAjaxCall("http://localhost:8000/images/", false);
        }
    });

    $("#prev").click(function(){
        if (global.currentData) {
            var size = global.currentData['results'].length;
            if(global.index - 1 >= 0){
                global.index = global.index - 1;
                loadNewImage();
            } else if(global.currentData['previous'] != null){

                makeAjaxCall(global.currentData['previous'], false);
                global.index = global.currentData['results'].length - 1;
            } else {
                console.log("First page.");
            }
        } else {
            makeAjaxCall("http://localhost:8000/images/", false);
        }
    });
    $("#submit").click(function(){



        if (global.currentData) {
            var extent = polygonFeature.getGeometry().getExtent();
            console.log(extent);

            var coordinate = [extent[2], extent[3]]; 

            var controls = "<div class='controls'><button class='btn submit-button damage' id='damage-submit'>Damaged</button><button class='btn submit-button no-damage' id='no-damage-submit'>Not Damaged</button></div";




            content.innerHTML = controls;
            overlay.setPosition(coordinate);
            


            var x = Math.round(extent[0]);
            var y = Math.round(height - (featureHeight + extent[1]));
            var w = featureWidth;
            var h = featureHeight;
            var uuid = uuidv4();
            var url = global.currentData['results'][global.index]['url'];
            var label = $("#label :selected").text();


            $("#damage-submit").click(function(){
                sendInfo(uuid, url, x, y, w, h, 'Presente');
                closePopup();
            });

            $("#no-damage-submit").click(function(){
                sendInfo(uuid, url, x, y, w, h, 'Ausente');
                closePopup();
            });
        }
    });
    $("#predict").click(function(){
        if (global.currentData) {
            var extent = polygonFeature.getGeometry().getExtent();
            var x = Math.round(extent[0]);
            var y = Math.round(height - (featureHeight + extent[1]));
            var w = featureWidth;
            var h = featureHeight;
            var uuid = uuidv4();
            
            $.ajax({
                url: "http://localhost:8000/images/"+global.currentData['results'][global.index]['pk']+"/"+x+"/"+y+"/"+h+"/"+w,
                type: "GET",
                dataType: "json",
                contentType: "application/json",
                success: function (data) {
                    console.log(data);
                    //window.alert("damage: " + data['damage'] + "\nno damage:" + data['nodamage']);
                    if(data['damage'] > .5){
                        $("#prediction").text("Daño")
                    } else {
                        $("#prediction").text("No Daño")
                    }
                    
                },
                beforeSend : function(req) {
                    req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
                    //curl -X GET http://127.0.0.1:8000/images/780/0/0/300/300 -H 'Authorization: Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd'
                }
            });
        }
    });
});