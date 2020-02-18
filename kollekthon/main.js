import { CountUp } from './countUp.min.js';

window.onload = function() {
  var xmlhttp = new XMLHttpRequest();
  var url = "total.json";

  xmlhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
          newval = JSON.parse(this.responseText).total;

          // newval = currentval + 1123;
          var countUp = new CountUp('total', newval, { startVal: currentval, duration: 2, separator:' ', suffix: " €" });
          currentval = newval;
          countUp.start();
      }
  };
  function updatetotal() {
    xmlhttp.open("GET", url + '?' + (new Date()).getTime(), true);
    xmlhttp.send();
  }

  window.setInterval(function() {
    updatetotal();
  }, 60000);
  updatetotal();
}
