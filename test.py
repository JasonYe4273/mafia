<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="icon" type = "image/jpg" href = "http://clipart-library.com/img/1762322.jpg" />
<title>  Mafia </title> </head>
</head>
<body>

<p> 
    <font style="font-size: 55px">
        Welcome to live action mafia! 
    </font> 
</p>

<button onclick="getLocation()">Log a kill!</button>

<p id="demo"></p>

<script>
var x = document.getElementById("demo");

function getLocation() {
  console.log("in");
  console.log(navigator.geolocation);
  if (navigator.geolocation) {
    console.log("present!")
    navigator.geolocation.getCurrentPosition(showPosition,errorTaker,{maximumAge:0, timeout:5000, enableHighAccuracy:false});
  } else { 
    x.innerHTML = "Geolocation not available";
  }
}

function showPosition(position) {
  console.log("trying");
  x.innerHTML = "Lat: " + position.coords.latitude + 
  "<br>Lon: " + position.coords.longitude;
}
function errorTaker(pos){
    console.log("damn");
    x.innerHTML = "Fail";
}
</script>

</body>
</html>