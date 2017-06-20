import logging
import gevent
from steam import SteamClient
from csgo import CSGOClient
from csgo.enums import ECsgoGCMsg
import struct
import os

import collections
import functools

class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

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
            LOG.info('steam login success')
            self.csgo.launch()

        @cs.on('ready')
        def gc_ready():
            LOG.info('launched csgo')
            pass

    def start(self):
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

    @memoized
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

        resp_iteminfo = resp[0].iteminfo
        paintwear = struct.unpack('f', struct.pack('i', resp_iteminfo.paintwear))[0]

        iteminfo = {
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
