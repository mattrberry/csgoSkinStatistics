from gevent.wsgi import WSGIServer
from csgo_worker import CSGOWorker
from flask import Flask, request, current_app

import os
import sys

import logging

logging.basicConfig(format="%(asctime)s | %(name)s | %(message)s",
                    level=logging.INFO)
LOG = logging.getLogger('CSGO GC API')

app = Flask('Flask Server')


@app.route('/')
def home():
    return current_app.send_static_file('index.html')


@app.route('/item', methods=["POST"])
def item() -> str:
    s = int(request.json['s'])
    a = int(request.json['a'])
    d = int(request.json['d'])
    m = int(request.json['m'])

    try:
        iteminfo = worker.get_item(s, a, d, m)
    except TypeError:
        LOG.info('Failed response')
        return 'Invalid link or Steam is slow.'

    return str(iteminfo)


@app.route('/ping', methods=["POST"])
def ping() -> str:
    return 'pong'


if __name__ == "__main__":
    LOG.info("csgoSkinStatistics")
    LOG.info("-" * 18)
    LOG.info("Starting worker...")

    worker = CSGOWorker()

    try:
        worker.start(username=os.environ['steam_user'],
                     password=os.environ['steam_pass'])
    except:
        LOG.info('Failed with environment variables. Trying args...')
        try:
            worker.start(username=sys.argv[1], password=sys.argv[2])
        except:
            LOG.info('Failed with args. Exiting...')
            sys.exit()

    LOG.info("Starting HTTP server...")
    http_server = WSGIServer(('', 5000), app, log=None)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Exit requested")
        worker.close()
