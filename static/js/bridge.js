var current = "";
var next = "";

function generateLocation() {
    console.log("generateLocation");
    navigator.geolocation.getCurrentPosition(receiveLocation);
    $('#status').html("Getting your current location...");
}

function receiveLocation(location) {
    console.log("receiveLocation");
    var lat = location.coords.latitude;
    var lon = location.coords.longitude;
    $('#status').html("Reverse geocoding...");
    $.get("https://maps.googleapis.com/maps/api/geocode/json?latlng=" + lat + "," + lon, function(data) {
        var address = data['results'][0]['formatted_address'];
        address = address.split(", ").slice(0, 2).join(", ");
        time = getTime();
        current = "Current location: " + address + " at " + time;
        generateNext(lat, lon);
    }, "json");
    $('#spinner').show();
}

function generateNext(lat, lon) {
    $('#status').html(current + "  <br /><br />Generating next location...");
    $.get("/" + lat + "," + lon, function(data) {
        data = data.split('*')
        var location = data[0];
        var time = data[1];
        next = "AI Next location: <a href='https://www.google.com/maps/place/" + location + "' target='_blank'>" + location + "</a> at " + time;
        $('#spinner').hide();
        $('#status').html(current + "<br /><br />" + next);
    });            
}

function getTime() {
    var date = new Date();
    var hours = date.getHours();
    var minutes = date.getMinutes();
    var ampm = hours >= 12 ? 'pm' : 'am';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    minutes = ('0' + minutes).slice(-2);
    var strTime = hours + ':' + minutes + ampm;
    return strTime;
}