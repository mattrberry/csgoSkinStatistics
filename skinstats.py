from getpass import getpass
from gevent.wsgi import WSGIServer
from csgo_worker import CSGOWorker
from flask import Flask, request, render_template

import os
import sys

import logging
logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s",
                    level=logging.INFO)
LOG = logging.getLogger('CSGO GC API')

app = Flask('Flask Server')


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

    return str(iteminfo)


if __name__ == "__main__":
    LOG.info("csgoSkinStatistics")
    LOG.info("-"*18)
    LOG.info("Starting worker...")

    worker = CSGOWorker()

    try:
        worker.start(username=os.environ['steam_user'],
                     password=os.environ['steam_pass'])
    except:
        try:
            worker.start(username=sys.argv[1], password=sys.argv[2])
        except:
            try:
                worker.start(username=input('Username: '), password=getpass())
            except:
                raise SystemExit

    LOG.info("Starting HTTP server...")
    http_server = WSGIServer(('', 5000), app)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Exit requested")
        worker.close()
