from flask import Flask, render_template, Markup, request
import os
from gevent.wsgi import WSGIServer
# from flask import Flask, request, abort, jsonify
from csgo_worker import CSGOWorker

import logging
logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s", level=logging.INFO)
LOG = logging.getLogger('csgo gc api')

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
    
    try:
        iteminfo = worker.send(s, a, d, m)
    except TypeError:
        return 'Invalid link or Steam is slow.'

    LOG.info('returning: {}'.format(str(iteminfo)))

    return str(iteminfo)

if __name__ == '__main__':
    LOG.info('simple csgo gc')
    LOG.info('--------------')
    LOG.info('starting worker')

    worker = CSGOWorker()

    worker.start()

    LOG.info('starting server')
    http_server = WSGIServer(('', 5000), app)

    try:
        http_server.serve_forever()
    except:
        LOG.info('exit requested')
        worker.close()
