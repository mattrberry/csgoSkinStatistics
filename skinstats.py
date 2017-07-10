from getpass import getpass
from gevent.wsgi import WSGIServer
from csgo_worker import CSGOWorker
from flask import Flask, request, abort, jsonify, render_template

import logging
logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s", level=logging.INFO)
LOG = logging.getLogger('SimpleWebAPI')

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


if __name__ == "__main__":
    LOG.info("Simple Web API recipe")
    LOG.info("-"*30)
    LOG.info("Starting Steam worker...")

    worker = CSGOWorker()

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
