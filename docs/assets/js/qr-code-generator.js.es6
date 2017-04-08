---
---


document.forms['get-qr'].onsubmit = function(e){
  e.preventDefault()
  const get_value = x => encodeURIComponent(document.querySelector(x).value)
  const ec = get_value('select[name="qr-ec"]')
  const data = get_value('textarea[name="qr-data"]')
  const url = `http://tjeu.pythonanywhere.com/qr.svg?qr-ec=${ec}&qr-data=${data}`
  document.getElementById('qr-img').setAttribute('src', url)
}
