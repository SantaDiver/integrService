function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie != '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

$(document).ready(function(){

$('.addform').click(function(event){
  event.preventDefault();
  var csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      xhr.setRequestHeader('X-CSRFToken', csrftoken);
    }
  });
  form_data = $('form').serializeArray();
  var data = {}
  for (var n in form_data) {
    if (form_data[n]['name'] == 'name') data['name'] = form_data[n]['value'];
  }
  
  var path = window.location.pathname;
  var arrVars = path.split("/");
  var type = arrVars[1];
  data['type'] = type;

  $.post('/newForm', JSON.stringify(data), function() {
    window.location.replace('/'+type+'/'+data['name']);
  }, 'json')
    .fail(function() {
      $('.invalid-name').show()
    });
});

  
});