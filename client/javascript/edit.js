var global = {};

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
        var url = global.currentData['results'][i]['url'];
        console.log(url);
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