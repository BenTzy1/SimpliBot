from flask import flask,render_template
from threading import Thread

app = Flask(_name_)

@app_route('/')
def index():
    return'alive'

def run():
    app.run(host='0.0.0.0', port='8080')

def keep_alive():
    t = thread(target=run)
    t.start()
