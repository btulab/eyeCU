var socket;
$(document).ready(function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);
  socket.on('connect', function() {
    $('#statusBar').prepend("<p id=status>Listening for network updates...</p>");
  });
  socket.on('update', function(data) {
    $('#statusBar').prepend("<p id=status>"+ data.msg +"</p>");
  });
});

