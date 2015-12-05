var countPed = 0;
var countBike = 0;
var pedButton = document.getElementById("countPedButton");
var bikeButton = document.getElementById("countBikeButton");
var start = document.getElementById("startButton");
var displayNumPed = document.getElementById("displayCountPed");   
var displayNumBike = document.getElementById("displayCountBike");
var buttonPedValue = document.getElementById("buttonPedValue");
var buttonBikeValue = document.getElementById("buttonBikeValue");
var countButtonField = document.getElementById("countButtons");
var startButtonField = document.getElementById("startButtonField");
var location = document.getElementById("location");

start.onclick = function(){
  countButtons.disabled = false;
  startButtons.disabled = true;
  if (location.value.length != 0) {
    display = document.querySelector('#time');
    startTimer(5, display);
  } else {
    $('#noLocationEntered').show();
  }
}
pedButton.onclick = function(){
  countPed++;
  displayNumPed.innerHTML = countPed;
}
bikeButton.onclick = function(){
  countBike++;
  displayNumBike.innerHTML = countBike;
}
function startTimer(duration, display) {
  var start = Date.now(),
  diff,
  minutes,
  seconds;
  function timer() {
  // get the number of seconds that have elapsed since 
  // startTimer() was called
  diff = duration - (((Date.now() - start) / 1000) | 0);
  // does the same job as parseInt truncates the float
  minutes = (diff / 60) | 0;
  seconds = (diff % 60) | 0;
  minutes = minutes < 10 ? "0" + minutes : minutes;
  seconds = seconds < 10 ? "0" + seconds : seconds;
  display.textContent = minutes + ":" + seconds; 
  if (diff <= 0) {
      // add one second so that the count down starts at the full duration
      // example 05:00 not 04:59
      start = Date.now() + 1000;
    }
  if (diff == 0) {
    buttonPedValue.value = countPed;
    buttonBikeValue.value = countBike;
    document.getElementById("counter").submit();
  }
  };
// we don't want to wait a full second before the timer starts
timer();
setInterval(timer, 1000);
}
//window.onload = function () {
//var fiveMinutes = 60 * 15,
//display = document.querySelector('#time');
//startTimer(10, display);
//};