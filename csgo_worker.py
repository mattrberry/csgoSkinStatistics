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

        @client.on('channel_secured')
        def send_login():
            if client.relogin_available:
                client.relogin()
            else:
                client.login(**self.logon_details)

        @client.on('logged_on')
        def start_csgo():
            self.csgo.launch()
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
        self.csgo.wait_event('ready')

    def close(self):
        if self.steam.connected:
            self.steam.logout()
        LOG.info('logged out')


    def send(self, s, a, d, m):
        LOG.info('sending s:{} a:{} d:{} m:{}'.format(s, a, d, m))

        self.csgo.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest, {
            'param_s': s,
            'param_a': a,
            'param_d': d,
            'param_m': m,
            })

        resp = self.csgo.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, timeout=1)
        
        if resp is None:
            LOG.info('csgo failed to respond')
            raise TypeError

        paintwear = str(struct.unpack('f', struct.pack('i', resp[0].iteminfo.paintwear))[0])

        LOG.info('paintwear: {}'.format(paintwear))

        return paintwear 
