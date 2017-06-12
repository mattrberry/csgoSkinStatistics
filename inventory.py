import requests
import json
import math
from flask import Flask, render_template, Markup, request
import time
from skinData import fades, order, doppler
import os

from steam import SteamClient
from csgo import CSGOClient
from csgo.enums import ECsgoGCMsg

import struct

client = SteamClient()
cs = CSGOClient(client)

@client.on('logged_on')
def start_csgo():
    print('launching csgo...')
    cs.launch()

@cs.on('ready')
def gc_ready():
    print('launched csgo')
    app.run()
    pass

def send(s, a, d, m):
    cs.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest, {
        'param_s': s,
        'param_a': a,
        'param_d': d,
        'param_m': m,
        })

    resp = cs.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, timeout = 10)

    try:
        return struct.unpack('f', struct.pack('i', resp[0].iteminfo.paintwear))
    except:
        return None

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html', info_location="")


@app.route('/displayInventory', methods=["POST"])
def displayInventory():
    s = int(request.form['s'])
    a = int(request.form['a'])
    d = int(request.form['d'])
    m = int(request.form['m'])

    print('s:{}, a:{}, d:{}, m:{}'.format(s, a, d, m))

    resp = None
    count = 0
    while resp is None and count < 2:
        print('count:' + str(count))
        resp = send(s, a, d, m)
        count += 1

    if resp is None:
        return 'Either Steam is slow or that\'s an invalid link'

    return str(resp[0])


def main(steamid, inspectid):
    timeStart = time.time()

    with open('json/itemDB.json') as f:
        itemDB = json.load(f, encoding='utf-8')

    with open('json/skinDB.json') as f:
        skinDB = json.load(f, encoding='utf-8')

    with open('json/patternDB.json') as f:
        patternDB = json.load(f, encoding='utf-8')


if __name__ == '__main__':
    client.login(os.environ['steam_user'], os.environ['steam_pass'])
    client.run_forever()
