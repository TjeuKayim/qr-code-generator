from flask import Flask, request
from qr import Qr_code

app = Flask(__name__)

@app.route("/")
def home():
    return '{"active":true}'

@app.route("/qr.svg")
def svg():
    data = request.args.get('qr-data', 'https://tjeukayim.github.io/qr-codes/')
    ec = request.args.get('qr-ec', 'H')
    if ec not in ['L', 'M', 'Q', 'H']: ec = 'H'
    return Qr_code(data, ec=ec).to_svg(), 200, {'Content-Type': 'image/svg+xml'}

if __name__ == "__main__":
    app.run()
