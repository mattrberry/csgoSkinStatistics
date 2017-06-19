import logging
import gevent
from steam import SteamClient
from csgo import CSGOClient
from csgo.enums import ECsgoGCMsg
import struct
import os

LOG = logging.getLogger('CSGO Worker')

class CSGOWorker(object):
    def __init__(self):
        self.steam = client = SteamClient()
        self.csgo = cs = CSGOClient(self.steam)

        @client.on('logged_on')
        def start_csgo():
            LOG.info('steam login success')
            LOG.info('launching csgo...')

        @cs.on('ready')
        def gc_ready():
            LOG.info('launched csgo')
            pass

    def start(self):
        LOG.info('attempting steam signin')

        self.logon_details = {
                'username': os.environ['steam_user'],
                'password': os.environ['steam_pass'],
                }

        self.steam.connect()
        self.steam.wait_event('logged_on')

    def close(self):
        if self.steam.connected:
            self.steam.logout()
        LOG.info('logged out')


    def send(self, s, a, d, m):
        LOG.info('sending s:{} a:{} d:{} m:{}'.format(s, a, d, m))

        cs.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest, {
            'param_s': s,
            'param_a': a,
            'param_d': d,
            'param_m': m,
            })

        resp = cs.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, timeout = 2)

        return struct.unpack('f', struct.pack('i', resp[0].iteminfo.paintwear))
