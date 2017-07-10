import logging
import gevent
from steam import SteamClient
from csgo import CSGOClient
from csgo.enums import ECsgoGCMsg
import struct
import os
import json
from skinData import fades, order, doppler

import collections
import functools


LOG = logging.getLogger("CSGO Worker")


class CSGOWorker(object):
    def __init__(self):
        self.steam = client = SteamClient()
        self.csgo = cs = CSGOClient(self.steam)

        self.request_method = ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest
        self.response_method = ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse

        with open('json/itemDB.json') as f:
            self.itemDB = json.load(f, encoding='utf-8')

        with open('json/skinDB.json') as f:
            self.skinDB = json.load(f, encoding='utf-8')

        with open('json/patternDB.json') as f:
            self.patternDB = json.load(f, encoding='utf-8')

        @client.on('channel_secured')
        def send_login():
            if client.relogin_available:
                client.relogin()
            else:
                client.login(**self.logon_details)

        @client.on('logged_on')
        def start_csgo():
            LOG.info('steam login success')
            self.csgo.launch()

        @cs.on('ready')
        def gc_ready():
            LOG.info('launched csgo')
            pass

    def start(self, username, password):
        self.logon_details = {
            'username': username,
            'password': password,
            }

        self.steam.connect()
        self.steam.wait_event('logged_on')
        self.csgo.wait_event('ready')

    def close(self):
        if self.steam.connected:
            self.steam.logout()
        LOG.info('logged out')

    def send(self, s, a, d, m):
        LOG.info('sending s:{} a:{} d:{} m:{}'.format(s, a, d, m))

        self.csgo.send(self.request_method, {
            'param_s': s,
            'param_a': a,
            'param_d': d,
            'param_m': m,
            })

        resp = self.csgo.wait_event(self.response_method, timeout=1)

        if resp is None:
            LOG.info('csgo failed to respond')
            raise TypeError

        resp_iteminfo = resp[0].iteminfo

        paintwear = struct.unpack('f', struct.pack('i', resp_iteminfo.paintwear))[0]
        weapon_type = self.itemDB['item'][str(resp_iteminfo.defindex)]
        pattern = self.skinDB['skin'][str(resp_iteminfo.paintindex)]
        name = "{} | {}".format(weapon_type, pattern)
        paintseed = resp_iteminfo.paintseed
        special = ""

        if pattern == "Marble Fade":
            try:
                special = self.patternDB[weapon_type][pattern][paintseed]
            except KeyError:
                LOG.info("non-indexed marble fade")
        elif pattern == "Fade" and weapon_type in fades:
            info = fades[weapon_type]
            unscaled = order[::info[1]].index(int(paintseed))
            scaled = unscaled / 1001
            percentage = round(info[0] + scaled * (100 - info[0]))
            special = str(percentage) + "%"
        elif pattern == "Doppler" or pattern == "Gamma Doppler":
            special = doppler[resp_iteminfo.paintindex]

        iteminfo = {
                'name':       name,
                'special':    special,
                'itemid':     resp_iteminfo.itemid,
                'defindex':   resp_iteminfo.defindex,
                'paintindex': resp_iteminfo.paintindex,
                'rarity':     resp_iteminfo.rarity,
                'quality':    resp_iteminfo.quality,
                'paintwear':  paintwear,
                'paintseed':  resp_iteminfo.paintseed,
                'inventory':  resp_iteminfo.inventory,
                'origin':     resp_iteminfo.origin,
                }

        return iteminfo
