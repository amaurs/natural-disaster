var global = {};



function deleteFactory(pk) {
    return function(){retrieveData(SERVER_URL + "/samples/" + pk + "/", "DELETE", reload);};
}

function updateFactory(pk) {
    return function(){retrieveData(SERVER_URL + "/samples/" + pk + "/", "PATCH", reload);};
}

function loadNewImage() {
    for(var i = 0; i < global.currentData['results'].length; i++) {
        var url = IMAGES_URL + "/thumb/" + global.currentData['results'][i]['name'];
        var label = global.currentData['results'][i]['label'].name;
        var pk = global.currentData['results'][i]['pk'];
        var $div = $("<div class='column is-one-fourth'></div> ");
        var $cardImage = $("<div class='card-image'></div> ");
        var $image = $("<figure class='image is-marginless'><img src='" + url + "'></figure>");
        var $controls = $("<div class='card-content'></div");

        var $media = $("<div class='media'></div");
        var $mediaLeft = $("<figure class='media-left'><p class='image is-32x32 " + (label!="Ausente"?"no-damage":"damaged") + "'></p></figure>");

        var $mediaContent = $("<div class='media-content'></div");
        var $delete = $("<button class='button is-small is-fullwidth'>Delete</button>");
        var $update = $("<button class='button is-small is-fullwidth'>Update</button>");
        



        $delete.click(deleteFactory(pk));
        $update.click(updateFactory(pk));
        $cardImage.append($image);
        $div.append($cardImage);
        

        $mediaContent.append($delete);
        $mediaContent.append($update);

        $media.append($mediaLeft);
        $media.append($mediaContent);

        $controls.append($media);

        $div.append($controls);
        $("#images").append($div);
    }
}

function paintSamplesFactory(load) {
    return function paintSamples(result) {
        global.currentData = result;
        if(load) { 
            global.index = 0;
            loadNewImage();
        }
    }
}

function makeAjaxCall(urlCall, load) {
    $.ajax({
        type: 'GET',
        url: urlCall,
        success: paintSamplesFactory(load),
        beforeSend : function(req) {
            req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}

$(document).ready(function(){
    var data;
    $("#title").text(getTownName());
    var urlCall = SERVER_URL + "/samples/list/" + getTownId() + "/?limit=10000";
    global.currentUrl = urlCall;
    retrieveData(urlCall, "GET", paintSamplesFactory(true));
    $("#next").click(function(){
        if(global.currentData['next'] != null) {
            $('#images').html('');
            urlCall = global.currentData['next'];
            retrieveData(urlCall, "GET", paintSamplesFactory(true));
        }
    });
    $("#prev").click(function(){
        if(global.currentData['previous'] != null) {
            $('#images').html('');
            urlCall = global.currentData['next'];
            retrieveData(urlCall, "GET", paintSamplesFactory(true));
        }
    });
});