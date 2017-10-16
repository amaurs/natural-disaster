var width = 4000;
var height = 3000;
var featureWidth = featureHeight = 322;
var extent = [0, 0, width, height];
var source = new ol.source.Vector({wrapX: false});
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

function make_base_auth(user, password) {
    var tok = user + ':' + password;
    console.log(tok);
    var hash = btoa(tok);
    return 'Basic ' + hash;
}

function getSource(newUrl) {
    var finalUrl = "http://127.0.0.1:8081/" + newUrl;
    newSource = new ol.source.ImageStatic({
                        url: finalUrl,
                        projection: projection,
                        imageExtent: extent
                    });
    return newSource;
}

function deleteFactory(pk) {
    return function deleteThumbnail() {
            console.log(pk);
            $.ajax({
                url: "http://localhost:8000/samples/" + pk + "/",
                type: "DELETE",
                success: function (data) {
                    console.log(data);
                    makeAjaxCall(global.currentUrl, true);
                },
                beforeSend : function(req) {
                    req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
                }
            });
        }
}

function loadNewImage() {
    console.log(global.currentData['results']);
    for(var i = 0; i < global.currentData['results'].length; i++) {

        var url = "http://192.168.15.2:8081/" + global.currentData['results'][i]['url'];
        var label = global.currentData['results'][i]['label'].name;
        var pk = global.currentData['results'][i]['pk'];

        var $div = $("<div  class=\"row\"></div> ");

        var $p = $("<div class=\"col-sd-4\">"+label+"</div>")

        var $image = $("<div  class=\"col-sd-4 thumbnail\"><img src='"+url+"'></div>");

        

        var $input = $('<div  class=\"col-sd-4\"><button class="btn">Delete</button></div>');
        

        $input.click(deleteFactory(pk));
        
        $div.append($p);
        $div.append($image);
        $div.append($input);


        $("#images").append($div);
    }


}

function makeAjaxCall(urlCall, load) {
    $.ajax({
        type: 'GET',
        url: urlCall, 
        success: function(result){
            global.currentData = result;
            global.currentUrl = urlCall;
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

$(document).ready(function(){
    
    var data;
    
    makeAjaxCall("http://localhost:8000/samples/", true);
    

    $("#next").click(function(){
        if(global.currentData['next'] != null) {
            $('#images').html('');
            makeAjaxCall(global.currentData['next'], true);
        }
    });

    $("#prev").click(function(){
        if(global.currentData['previous'] != null) {
            $('#images').html('');
            makeAjaxCall(global.currentData['previous'], true);
        }
    });
    
});