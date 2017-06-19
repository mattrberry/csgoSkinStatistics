from flask import Flask, render_template, Markup, request
import os
from gevent.wsgi import WSGIServer
# from flask import Flask, request, abort, jsonify
from csgo_worker import CSGOWorker

import logging
logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s", level=logging.INFO)
LOG = logging.getLogger('CSGO GC API')

app = Flask('CSGO GC API')


@app.route('/')
def home():
    return render_template('index.html', info_location="")


@app.route('/displayInventory', methods=["POST"])
def displayInventory():
    s = int(request.form['s'])
    a = int(request.form['a'])
    d = int(request.form['d'])
    m = int(request.form['m'])
    
    paintwear = None

    for i in range(1):
        try:
            paintwear = worker.send(s, a, d, m)
            break
        except:
            pass

    if not paintwear:
        paintwear = 'Invalid link or Steam is slow.'
 
    return paintwear


if __name__ == '__main__':
    LOG.info('Simple CSGO GC')
    LOG.info('---------------')
    LOG.info('Starting worker')

    worker = CSGOWorker()

    worker.start()

    LOG.info('Starting server')
    http_server = WSGIServer(('', 5000), app)

    try:
        http_server.serve_forever()
    except:
        LOG.info('Exit requested')
        worker.close()
