var SERVER_URL = "http://127.0.0.1:8000";
var IMAGES_URL = "http://127.0.0.1:8081";

var appId = 'oD5a07ufBWFGUSdPa4k0';
var appCode = 'ASjZ3JbFVY7RPCHYbOB08A';

var hereLayers = [
  {
    base: 'base',
    type: 'maptile',
    scheme: 'normal.day',
    app_id: appId,
    app_code: appCode
  },
  {
    base: 'base',
    type: 'maptile',
    scheme: 'normal.day.transit',
    app_id: appId,
    app_code: appCode
  },
  {
    base: 'base',
    type: 'maptile',
    scheme: 'pedestrian.day',
    app_id: appId,
    app_code: appCode
  },
  {
    base: 'aerial',
    type: 'maptile',
    scheme: 'terrain.day',
    app_id: appId,
    app_code: appCode
  },
  {
    base: 'aerial',
    type: 'maptile',
    scheme: 'satellite.day',
    app_id: appId,
    app_code: appCode
  },
  {
    base: 'aerial',
    type: 'maptile',
    scheme: 'hybrid.day',
    app_id: appId,
    app_code: appCode
  }
];
var urlTpl = 'https://{1-4}.{base}.maps.cit.api.here.com' +
  '/{type}/2.1/maptile/newest/{scheme}/{z}/{x}/{y}/256/png' +
  '?app_id={app_id}&app_code={app_code}';


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

function createUrl(tpl, layerDesc) {
  console.log(tpl);
  return tpl
      .replace('{base}', layerDesc.base)
      .replace('{type}', layerDesc.type)
      .replace('{scheme}', layerDesc.scheme)
      .replace('{app_id}', layerDesc.app_id)
      .replace('{app_code}', layerDesc.app_code);
}

function getTownName() {
    var names = {
        1:"Unión Hidalgo",
        2:"Juchitán de Zaragoza",
        3:"Santa María Xadani"}
    return names[getTownId()];
}

function getTownIdFromName(name) {
    var names = {
        "Unión Hidalgo":1,
        "Juchitán de Zaragoza":2,
        "Santa María Xadani":3}
    return names[name];
}

function townStyle(town) {
    var style = new ol.style.Style({
        image: new ol.style.Circle({
            radius: 6,
            fill: new ol.style.Fill({
                color: town==3?'#ffeda0':
                       town==1?'#feb24c':
                               '#f03b20'
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