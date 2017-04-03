from flask import Flask, request
from qr import Qr_code

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!!!"

@app.route("/qr.svg")
def svg():
    data = request.cookies.get('qr-data', default='')
    data = 'Test'
    if data == '': return
    ec = request.cookies.get('qr-ec', default='H')
    return Qr_code(data, ec=ec).to_svg()

if __name__ == "__main__":
    app.run()
