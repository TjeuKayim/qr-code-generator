document.forms['get-qr'].onsubmit = function(e){
  e.preventDefault()
  var get_value = function(x) {return encodeURIComponent(document.querySelector(x).value)}
  var ec = get_value('select[name="qr-ec"]')
  var data = get_value('textarea[name="qr-data"]')
  var url = 'https://tjeu.pythonanywhere.com/qr.svg?qr-ec=' + ec + '&qr-data=' + data
  document.getElementById('qr-img').setAttribute('src', url)
}

Element.prototype.drag = function(){
  var mousemove = function(e){ // document mousemove
      this.style.left = (e.clientX - .5*this.offsetWidth)+'px'
      this.style.top  = (e.clientY - .5*this.firstChild.offsetHeight)+'px'
  }.bind(this)

  var mouseup = function(e){ // document mouseup
      document.removeEventListener('mousemove',mousemove)
      document.removeEventListener('mouseup',mouseup)
      document.body.style.cursor = ''
  }.bind(this)

  this.firstChild.addEventListener('mousedown',function(e){ // element mousedown
      document.addEventListener('mousemove',mousemove)
      document.addEventListener('mouseup',mouseup)
      document.body.style.cursor = 'grabbing'
      e.preventDefault()
  }.bind(this))
}

function showDragMe() {
  var dragMe = document.getElementById('drag-me')
  dragMe.style.display = 'block'
  dragMe.drag()
}
