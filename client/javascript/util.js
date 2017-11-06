var SERVER_URL = "http://127.0.0.1:8000";
var IMAGES_URL = "http://127.0.0.1:8081";

function getParam(param){
    return new URLSearchParams(window.location.search).get(param);
}

function getTownId() {
    var townId = getParam("town_id");
    if (townId == null){
        townId = 1;
    }
    return townId;
}

function getTownName() {
    var names = {1:"Unión Hidalgo",
     2:"Juchitán de Zaragoza",
     3:"Santa María Xadani"}
    return names[getTownId()];
}

function calculateCentroid(coords) {
    var longitude = 0;
    var latitude = 0;
    for (var i = 0; i < coords.length; i++) {
        longitude += coords[i][0];
        latitude += coords[i][1];
    }
    return [longitude / coords.length, latitude / coords.length];
}