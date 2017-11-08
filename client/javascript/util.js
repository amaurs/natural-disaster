var SERVER_URL = "http://127.0.0.1:8000";
var IMAGES_URL = "http://127.0.0.1:8081";

function getParam(param){
    return new URLSearchParams(window.location.search).get(param);
}

function reload() {
    location.reload();
}

function getTownId() {
    var townId = getParam("town_id");
    if (townId == null){
        townId = 1;
    }
    return townId;
}

function getTownName() {
    var names = {
        1:"Unión Hidalgo",
        2:"Juchitán de Zaragoza",
        3:"Santa María Xadani"}
    return names[getTownId()];
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

function getView() {
    var center = [-94.83657579261286, 16.47216369265396];
    return new ol.View({
            projection: 'EPSG:4326',
            center: center,
            zoom: 15,
            minZoom: 14,
            maxZoom: 19
        });
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

function retrieveData(urlCall, method, onSuccess) {
    $.ajax({
        type: method,
        url: urlCall, 
        success: onSuccess,
        beforeSend : function(req) {
            req.setRequestHeader('Authorization', 'Token b2258391a854407d8e623c3a59ed4a95ef4ae9dd');
        },
    });
}