from flask import Flask, render_template, Markup, request
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

    resp = cs.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, timeout = 1)

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
    while resp is None and count < 3:
        resp = send(s, a, d, m)
        count += 1

    if resp is None:
        return 'Tried 3 times. Link is probably invalid.'

    return str(resp[0])


if __name__ == '__main__':
    client.login(os.environ['steam_user'], os.environ['steam_pass'])
    client.run_forever()
