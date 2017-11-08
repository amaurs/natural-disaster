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
        var $div = $("<div class='card " + (label=="Ausente"?"no-damage":"damage") +"'></div> ");
        var $image = $("<img class='thumbnail' src='" + url + "'>");
        var $controls = $("<div class='controls'></div")
        var $delete = $("<button class='btn edit-button'>Delete</button>");
        var $update = $("<button class='btn edit-button'>Update</button>");
        $delete.click(deleteFactory(pk));
        $update.click(updateFactory(pk));
        $div.append($image);
        $controls.append($delete);
        $controls.append($update);
        $div.append($controls);
        $("#images").append($div);
    }
}

function paintSamplesFactory(load) {
    return function paintSamples(result) {
        global.currentData = result;
        
        //Needs to be checked, this is clearly a hack.
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
            req.setRequestHeader('Authorization',  'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}

$(document).ready(function(){
    var data;
    $("#title").text("Edit " + getTownName());
    var urlCall = SERVER_URL + "/samples/list/" + getTownId() + "/";
    global.currentUrl = urlCall;
    retrieveData(urlCall, "GET", paintSamplesFactory(true))
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