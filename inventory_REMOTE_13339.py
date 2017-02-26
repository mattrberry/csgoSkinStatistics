import requests
import json
import math
from flask import Flask, render_template, Markup, request
import time
from skinData import fades, order, doppler

with open('steam_api_key') as f:
    apikey = f.read().strip()


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html', info_location="")


@app.route('/displayInventory', methods=["POST"])
def displayInventory():
    userinput = request.form['input']
    steamid = request.form['id']
    inspectid = request.form['itemid']

    try:
        response = main(convertID(str(steamid)), str(inspectid))
    except KeyError:
        response = ("<p style=\"text-align:center\">" +
                    "This Steam ID appears not to exist or it is private.<br>" +
                    "If you're absolutely sure that this is incorrect, try again in a few seconds.<br>" +
                    "If the error persists, use the \"Contact me.\" button below.<br>" +
                    "</p>")
            
    return response


def convertID(steamid):
    if not steamid.isdigit():
        url = ("http://api.steampowered.com/ISteamUser/ResolveVanityURL/" +
               "v0001/?key=" + apikey + "&vanityurl=" + steamid)
        response = requests.get(url)
        steamid = json.loads(response.text)['response']['steamid']
    return steamid


def main(steamid, inspectid):
    timeStart = time.time()

    url = ("http://api.steampowered.com/IEconItems_730/GetPlayerItems/" +
           "v0001/?key=" + apikey + "&SteamID=" + steamid)

    steamAPIcalls = 0
    while True:
        response = requests.get(url)
        if response.text != "{\n\n}":
            break
        elif steamAPIcalls >= 50:
            return "Steam API appears to be slow."

    playerItems = json.loads(response.text)

    with open('json/itemDB.json') as f:
        itemDB = json.load(f, encoding='utf-8')

    with open('json/skinDB.json') as f:
        skinDB = json.load(f, encoding='utf-8')

    with open('json/patternDB.json') as f:
        patternDB = json.load(f, encoding='utf-8')

    skins = []
    inspect = []
    keys = {}

    for item in playerItems["result"]["items"]:
        itemID = item["id"]
        itemType = item["defindex"]
        try:
            itemName = itemDB["item"][str(itemType)]
        except KeyError:
            itemName = "graffiti"  # pass

        if (itemType <= 516 or itemType in range(5027,5035)) and item["attributes"][0]["defindex"] == 6:
            patternIndex = item["attributes"][0]["float_value"]
            pattern = skinDB["skin"][str(patternIndex)]
            paintIndex = str(int(item["attributes"][1]["float_value"]))
            floatValue = item["attributes"][2]["float_value"]

            special = ""

            if pattern == "Marble Fade":
                try:
                    special = patternDB[itemName][pattern][paintIndex]
                except KeyError:
                    pass
            elif pattern == "Fade" and itemName in fades:
                info = fades[itemName]
                unscaled = (order.index(int(paintIndex)) * info[1]) % 1000
                scaled = unscaled / 1000
                percentage = round(info[0] + scaled * (100 - info[0]))
                special = str(percentage) + "%"
            elif pattern == "Doppler" or pattern == "Gamma Doppler":
                special = doppler[patternIndex]

            for attribute in item["attributes"]:
                if attribute["defindex"] == 81:
                    itemName = ("<span class=\"pop\">StatTrak</span> " +
                                itemName)
                    break

            if itemType >= 500:
                itemName = ("<span class=\"pop\">" + u'\u2605 ' +
                            "</span>" + itemName)

            skin = [itemName, pattern, special, floatValue]
            skins.append(skin)

            if str(itemID) == inspectid:
                inspect.append(skin)

        elif "Key" in itemName:
            if itemName in keys:
                keys[itemName] += 1
            else:
                keys[itemName] = 1

    if inspectid != "none" and len(inspect) < 1:
        inspect.append(["No longer in this inventory.", "", "", -1])


    return ("<table>" + inspectString(inspect) + skinString(skins) +
            keyString(keys) + "</table>")


def inspectString(inspect):
    try:
        inspectString = "<tr><th>Inspected Item</th><th>Float</th></tr>"
        if inspect[0][3] > 0:
            inspectString += outputWeapon(inspect)
        else:
            inspectString += "<tr><td>" + inspect[0][0] + "</td><td></td></tr>"
    except:
        inspectString = ""
        
    return inspectString

def skinString(skins):
    skinString = ""

    if len(skins) != 0:
        skinString += "<tr><th>Skins</th>"
        skinString += ("<th>" + str(len(skins)) + "</th></tr>")
        skinString += outputWeapon(skins)

    return skinString


def outputWeapon(weapons):
    weapons = sortFloat(weapons)
    weaponString = ""

    for weapon in weapons:
        weaponString += ("<tr><td>" + weapon[0] + " | " + weapon[1] +
                         "<sup><span style=\"font-size:12px\" class=\"pop\"> " +
                         weapon[2] + "</span></sup></td>" +
                         "<td>" + "{0:.12f}".format(weapon[3]) + "</td></tr>")

    return weaponString


def sortFloat(skns):
    floats = [skn[3] for skn in skns]
    return [s for (f, s) in sorted(zip(floats, skns))]


def keyString(keys):
    keyList = sortKeys(keys)
    keyString = ""

    if len(keyList) != 0:
        keyString += ("<tr><th>Keys</th><th>" +
                      str(sum([keys[k] for k in keys])) +
                      "</th></tr>")

        for key in keyList:
            keyString += ("<tr><td>" + key[0] + "</td>" +
                          "<td>" + str(key[1]) + "</td></tr>")

    return keyString


def sortKeys(keys):
    keyList = [[key, keys[key]] for key in keys]
    counts = [c for (n, c) in keyList]
    return [k for (c, k) in sorted(zip(counts, keyList))[::-1]]

if __name__ == '__main__':
    app.run()
