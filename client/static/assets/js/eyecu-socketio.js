var socket;

$(document).ready(function() {
  var socket = io.connect('http://' + document.domain + ':' + location.port);
// update messages
  socket.on('update', function(data) {
    $('#statusBar').prepend("<p class='anim-typewriter' id='status'>"+ data.msg +"</p>");
  });
});

