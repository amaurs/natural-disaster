var global = {};

function deleteFactory(pk) {
    return function deleteThumbnail() {
        $.ajax({
            url: SERVER_URL + "/samples/" + pk + "/",
            type: "DELETE",
            success: function (data) {
                console.log(data);
                location.reload();
            },
            beforeSend : function(req) {
                req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
            }
        });
    }
}

function updateFactory(pk) {
    return function updateThumbnail() {
        $.ajax({
            url: SERVER_URL + "/samples/" + pk + "/",
            type: "PATCH",
            success: function (data) {
                console.log(data);
                location.reload();
            },
            beforeSend : function(req) {
                req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
            }
        });
    }
}

function loadNewImage() {
    for(var i = 0; i < global.currentData['results'].length; i++) {
        var url = global.currentData['results'][i]['url'];
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

$(document).ready(function(){
    var data;
    makeAjaxCall(SERVER_URL + "/samples/list/" + getTownId() + "/", true);
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