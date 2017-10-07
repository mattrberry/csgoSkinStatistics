import logging
import gevent
from steam import SteamClient
from csgo import CSGOClient
from csgo.enums import ECsgoGCMsg
import struct
import os
import const
import json

import ast


LOG = logging.getLogger("CSGO Worker")


class CSGOWorker(object):
    def __init__(self):
        self.steam = client = SteamClient()
        self.csgo = cs = CSGOClient(self.steam)

        self.request_method = ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest
        self.response_method = ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse

        @client.on('channel_secured')
        def send_login():
            if client.relogin_available:
                client.relogin()
            else:
                client.login(**self.logon_details)

        @client.on('logged_on')
        def start_csgo():
            LOG.info('Logged into Steam')
            self.csgo.launch()

        @cs.on('ready')
        def gc_ready():
            LOG.info('Launched CSGO')
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
        LOG.info('Logged out')

    def send(self, s, a, d, m):
        LOG.info('Checking item {}'.format(a))

        with open('searches.txt') as searches:
            for search in searches:
                if search.split()[0] == str(a):
                    LOG.info('Found item {} in searches.txt'.format(a))
                    return ' '.join(search.split()[1:])

        LOG.info('Sending s:{} a:{} d:{} m:{} to GC'.format(s, a, d, m))

        self.csgo.send(self.request_method, {
            'param_s': s,
            'param_a': a,
            'param_d': d,
            'param_m': m,
            })

        resp = self.csgo.wait_event(self.response_method, timeout=1)

        if resp is None:
            LOG.info('CSGO failed to respond')
            raise TypeError

        resp_iteminfo = resp[0].iteminfo

        paintwear = struct.unpack('f', struct.pack('i',
                                                   resp_iteminfo.paintwear))[0]
        weapon_type = const.items[str(resp_iteminfo.defindex)]
        try:
            pattern = const.skins[str(resp_iteminfo.paintindex)]
        except:
            if resp_iteminfo.paintindex > 0:
                LOG.info('Pattern {} missing from database')
                pattern = str(resp_iteminfo.paintindex)
            else:
                pattern = 'Vanilla'
        name = "{} | {}".format(weapon_type, pattern)
        paintseed = str(resp_iteminfo.paintseed)
        special = ""

        if pattern == "Marble Fade":
            try:
                LOG.info(weapon_type)
                special = const.marbles[weapon_type][paintseed]
            except KeyError:
                LOG.info("Non-indexed marble fade")
        elif pattern == "Fade" and weapon_type in const.fades:
            info = const.fades[weapon_type]
            unscaled = const.order[::info[1]].index(int(paintseed))
            scaled = unscaled / 1001
            percentage = round(info[0] + scaled * (100 - info[0]))
            special = str(percentage) + "%"
        elif pattern == "Doppler" or pattern == "Gamma Doppler":
            special = const.doppler[resp_iteminfo.paintindex]

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

        with open('searches.txt', 'a') as searches:
            searches.write(str(a) + ' ' + json.dumps(iteminfo) + '\n')

        return json.dumps(iteminfo)
