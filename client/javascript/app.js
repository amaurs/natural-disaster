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
    console.log(global.currentData['results'][global.index]);
    source = getSource(IMAGES_URL + "/images/" + global.currentData['results'][global.index]['name']);
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

function sendInfo(uuid, url, name, x, y, w, h, label) {
    $.ajax({
        url: SERVER_URL + "/samples/",
        type: "POST",
        data: JSON.stringify({
            "name": uuid + ".jpg",
            "url": IMAGES_URL + "/thumb/" + uuid + ".jpg",
            "image": {
                "url": url,
                "name": name
            },
            "height": h,
            "width": w,
            "y": y,
            "x": x,
            "label": {
                "name": label
            },
            "town": {
                "name": getTownName()
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

function previous() {
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
        makeAjaxCall(SERVER_URL + "/images/" + getTownId() + "/", false);
    }
}

function next() {
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
        makeAjaxCall(SERVER_URL + "/images/" + getTownId() + "/", false);
    }
}

function submit() {
    if (global.currentData) {
        var extent = polygonFeature.getGeometry().getExtent();
        console.log(extent);
        var coordinate = [extent[2], extent[3]]; 
        var controls = "<div class='controls'><button class='button is-fullwidth damaged' id='damage-submit'>Damaged</button><button class='button no-damage is-fullwidth' id='no-damage-submit'>Not Damaged</button></div";
        content.innerHTML = controls;
        overlay.setPosition(coordinate);
        var x = Math.round(extent[0]);
        var y = Math.round(height - (featureHeight + extent[1]));
        var w = featureWidth;
        var h = featureHeight;
        var uuid = uuidv4();
        var url = global.currentData['results'][global.index]['url'];
        var name = global.currentData['results'][global.index]['name'];
        var label = $("#label :selected").text();


        $("#damage-submit").click(function(){
            sendInfo(uuid, url, name, x, y, w, h, 'Presente');
            closePopup();
        });

        $("#no-damage-submit").click(function(){
            sendInfo(uuid, url, name, x, y, w, h, 'Ausente');
            closePopup();
        });
    }
}

$(document).keydown(function(e) {
    if(e.which == 13) {
        submit();
    }
    if(e.which == 37) {
        previous();
    }
    if(e.which == 39) {
        next();
    }
});

$(document).ready(function(){
    var data;
    $("#title").text(getTownName());
    makeAjaxCall(SERVER_URL + "/images/" + getTownId() + "/", true);
    $("#next").click(next);
    $("#prev").click(previous);
    $("#submit").click(submit);
});

