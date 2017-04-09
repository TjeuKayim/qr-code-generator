document.forms['get-qr'].onsubmit = function(e){
  e.preventDefault()
  var get_value = function(x) {return encodeURIComponent(document.querySelector(x).value)}
  var ec = get_value('select[name="qr-ec"]')
  var data = get_value('textarea[name="qr-data"]')
  var url = 'https://tjeu.pythonanywhere.com/qr.svg?qr-ec=' + ec + '&qr-data=' + data
  document.getElementById('qr-img').setAttribute('src', url)
}
