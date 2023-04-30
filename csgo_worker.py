import logging
from steam.client import SteamClient
from csgo.client import CSGOClient
from csgo.enums import ECsgoGCMsg
import struct
import const
import json
import sqlite3
from time import time
from typing import Tuple


LOG = logging.getLogger("CSGO Worker")


class CSGOWorker(object):
    def __init__(self):
        self.steam = client = SteamClient()
        self.steam.cm_servers.bootstrap_from_webapi()
        self.csgo = cs = CSGOClient(self.steam)

        self.request_method = (
            ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest
        )
        self.response_method = (
            ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse
        )

        self.connection = sqlite3.connect("searches.db")
        self.cursor = self.connection.cursor()
        LOG.info("Connected to database")

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS searches (
                itemid integer NOT NULL PRIMARY KEY,
                defindex integer NOT NULL,
                paintindex integer NOT NULL,
                rarity integer NOT NULL,
                quality integer NOT NULL,
                paintwear real NOT NULL,
                paintseed integer NOT NULL,
                inventory integer NOT NULL,
                origin integer NOT NULL,
                stattrak integer NOT NULL,
                timestamp integer DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )

        self.logon_details = None

        @client.on("channel_secured")
        def send_login():
            if client.relogin_available:
                client.relogin()
            elif self.logon_details is not None:
                client.login(**self.logon_details)

        @client.on("logged_on")
        def start_csgo():
            LOG.info("Logged into Steam")
            self.csgo.launch()

        @cs.on("ready")
        def gc_ready():
            LOG.info("Launched CSGO")
            pass

    # Start the worker
    def start(self, username: str, password: str):
        self.logon_details = {
            "username": username,
            "password": password,
        }

        self.steam.connect()
        self.steam.wait_event("logged_on")
        self.logon_details = None
        self.csgo.wait_event("ready")

    # CLI login
    def cli_login(self):
        self.steam.cli_login()
        self.csgo.wait_event("ready")

    # Close the worker
    def close(self):
        self.connection.close()
        LOG.info("Database closed")
        if self.steam.connected:
            self.steam.logout()
            LOG.info("Logged out of Steam")

    # Lookup the weapon name/skin and special attributes. Return the relevant data formatted as JSON
    def form_response(
        self,
        itemid: int,
        defindex: int,
        paintindex: int,
        rarity: int,
        quality: int,
        paintwear: float,
        paintseed: int,
        inventory: int,
        origin: int,
        stattrak: int,
        timestamp: int,
    ) -> str:
        defindex_str = str(defindex)
        weapon_type = const.items.get(defindex_str, defindex_str)
        if weapon_type is defindex_str:
            LOG.warn(f"Item {defindex_str} is missing from constants")

        paintindex_str = str(paintindex)
        pattern = const.skins.get(paintindex_str, paintindex_str)
        if pattern is paintindex_str:
            LOG.warn(f"Skin {paintindex_str} is missing from constants")

        special = ""
        if pattern == "Marble Fade" and weapon_type in const.marbles:
            special = const.marbles[weapon_type].get(str(paintseed), special)
            if not special:
                LOG.info("Non-indexed %s | Marble Fade" % weapon_type)
        elif pattern == "Fade" and weapon_type in const.fades:
            minimum_fade_percent, order_reversed = const.fades[weapon_type]
            fade_index = const.order.index(paintseed)
            if order_reversed:
                fade_index = 1000 - fade_index
            actual_fade_percent = fade_index / 1001
            scaled_fade_percent = round(
                minimum_fade_percent
                + actual_fade_percent * (100 - minimum_fade_percent),
                1,
            )
            special = str(scaled_fade_percent) + "%"
        elif pattern == "Doppler" or pattern == "Gamma Doppler":
            special = const.doppler[paintindex]

        return json.dumps(
            {
                "itemid": itemid,
                "defindex": defindex,
                "paintindex": paintindex,
                "rarity": rarity,
                "quality": quality,
                "paintwear": paintwear,
                "paintseed": paintseed,
                "inventory": inventory,
                "origin": origin,
                "stattrak": stattrak,
                "weapon": weapon_type,
                "skin": pattern,
                "special": special,
            }
        )

    # Get relevant information from database xor game coordinator, then return the formated data
    def get_item(self, s: int, a: int, d: int, m: int) -> str:
        in_db = self.cursor.execute(
            "SELECT * FROM searches WHERE itemid = ?", (a,)
        ).fetchall()

        if len(in_db) == 0:
            LOG.info("Sending s:{} a:{} d:{} m:{} to GC".format(s, a, d, m))
            return self.form_response(*self.send(s, a, d, m))
        else:
            LOG.info("Found {} in database".format(a))
            return self.form_response(*in_db[0])

    # Send the item to the game coordinator and return the response data in a Tuple
    def send(
        self, s: int, a: int, d: int, m: int
    ) -> Tuple[int, int, int, int, int, float, int, int, int, int, int]:
        self.csgo.send(
            self.request_method,
            {
                "param_s": s,
                "param_a": a,
                "param_d": d,
                "param_m": m,
            },
        )

        resp = self.csgo.wait_event(self.response_method, timeout=1)

        if resp is None:
            LOG.error("CSGO failed to respond")
            raise TypeError

        iteminfo = resp[0].iteminfo

        paintwear = struct.unpack("f", struct.pack("i", iteminfo.paintwear))[0]
        stattrak = 1 if "killeatervalue" in str(iteminfo) else 0

        if "paintwear" not in str(iteminfo):
            raise TypeError

        values = (
            iteminfo.itemid,
            iteminfo.defindex,
            iteminfo.paintindex,
            iteminfo.rarity,
            iteminfo.quality,
            paintwear,
            iteminfo.paintseed,
            iteminfo.inventory,
            iteminfo.origin,
            stattrak,
        )

        result = self.cursor.execute(
            """
            INSERT INTO searches (itemid, defindex, paintindex, rarity, quality, paintwear, paintseed, inventory, origin, stattrak)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            values,
        ).fetchall()
        self.connection.commit()

        LOG.info("Added ID: {} to database".format(a))

        return result[0]
