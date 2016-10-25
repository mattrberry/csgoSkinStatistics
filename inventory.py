import requests, json, math
from flask import Flask, render_template, Markup, request
import time

with open('../steam_api_key') as f:
    apikey = f.read().strip()
      

app = Flask(__name__)

@app.route('/displayInventory', methods=["POST"])
def displayInventory():
    userinput  = request.form['input']
    steamid    = request.form['id']
    itemid     = request.form['itemid']

    response = main(convertID(str(steamid)))
    return response
    
def convertID(steamid):
    if not steamid.isdigit():
        url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=" + apikey + "&vanityurl=" + steamid
        response = requests.get(url)
        steamid = json.loads(response.text)['response']['steamid']
    return steamid
        
@app.route('/')
def home():
    return render_template('index.html', info_location="")

def main(steamid):
    timeStart = time.time()
    
    #steamid = str(76561198261551396)    # mattrb
    #steamid = str(76561197972331023)    # lololguardian

    with open('../steam_api_key') as f:
        apikey = f.read().strip()

    url = "http://api.steampowered.com/IEconItems_730/GetPlayerItems/v0001/?key=" + apikey + "&SteamID=" + steamid

    steamAPIcalls = 0
    while True:
        response = requests.get(url)
        if response.text != "{\n\n}":
            break
        elif steamAPIcalls >= 50:
            return "Tell Steam to fix their fucking API"

    playerItems = json.loads(response.text)

    with open('json/itemDB.json') as f:
        itemDB = json.load(f, encoding='utf-8')

    with open('json/skinDB.json') as f:
        skinDB = json.load(f, encoding='utf-8')

    with open('json/patternDB.json') as f:
        patternDB = json.load(f, encoding='utf-8')
    
    skins = []
    keys  = {}

    for item in playerItems["result"]["items"]:
        itemID   = item["id"]
        itemType = item["defindex"]
        try:
            itemName = itemDB["item"][str(itemType)]
        except:
            itemName = "graffiti" ### pass ###
            
        if itemType <= 516 and item["attributes"][0]["defindex"] == 6:
            patternIndex = item["attributes"][0]["float_value"]
            pattern      = skinDB["skin"][str(patternIndex)]
            paintIndex   = str(int(item["attributes"][1]["float_value"]))
            floatValue   = item["attributes"][2]["float_value"]
            
            special = ""

            if pattern == "Fade":
                if itemName == "Karambit":
                    special = patternDB["karambit"]["fade"][paintIndex] + "%"
                elif itemName == "Flip Knife":
                    special = patternDB["flip"]["fade"][paintIndex] + "%"
                elif itemName == "M9 Bayonet":
                    special = patternDB["m9"]["fade"][paintIndex] + "%"
            elif pattern == "Marble Fade":
                if itemName == "Karambit":
                    special = patternDB["karambit"]["marble"][paintIndex]
                elif itemName == "Bayonet" or itemName == "Gut Knife":
                    special = patternDB["bayonet"]["marble"][paintIndex]
                elif itemName == "Flip Knife":
                    special = patternDB["flip"]["marble"][paintIndex]
            elif pattern == "Doppler" or pattern == "Gamma Doppler":
                if patternIndex == 415:
                    special = "Ruby"
                elif patternIndex == 416:
                    special = "Sapphire"
                elif patternIndex == 417:
                    special = "Black Pearl"
                elif patternIndex == 418 or patternIndex == 569:
                    special = "Phase 1"
                elif patternIndex == 419 or patternIndex == 570:
                    special = "Phase 2"
                elif patternIndex == 420 or patternIndex == 571:
                    special = "Plase 3"
                elif patternIndex == 421 or patternIndex == 572:
                    special = "Phase 4"
                elif patternIndex == 568:
                    special = "Emerald"
                    
            for attribute in item["attributes"]:
              if (attribute["defindex"] == 81):
                itemName = "<span class=\"text-pop\">StatTrak</span> " +  itemName;
                break;

            if itemType >= 500:
                itemName = "<span class=\"text-pop\">" + u'\u2605 ' + "</span>" + itemName

            skin = [itemName, pattern, special, floatValue]

            skins.append(skin)
        elif "Key" in itemName:
            if itemName in keys:
                keys[itemName] += 1
            else:
                keys[itemName] = 1

    # timeTotal = time.time() - timeStart
    # loadTimeHTML = "<div style=\"text-align:center\">" + "Loaded in " + str(round(timeTotal,2)) + " seconds" + "</div>"
    
    #output = Markup("<table>" + convertSkinString(skins) + convertKeyString(keys) + "</table>" + loadTimeHTML)
    # return render_template('index.html', info_location=output), 200

    return ("<table>" + convertSkinString(skins) + convertKeyString(keys) + "</table>")
    
def convertSkinString(skns):
    skinString = ""

    if len(skns) != 0:
        skinString += "<tr><th>Skins</th>"
        skinString += ("<th>" + str(len(skns)) + "</th></tr>")
        skinString += outputWeapon(skns)

    return skinString

def outputWeapon(weapons):
    weapons = sortFloat(weapons)
    weaponString = ""

    for weapon in weapons:
        weaponString += ("<tr><td>" + weapon[0] + " | " + weapon[1] + "<sup><span style=\"font-size:12px\" class=\"text-pop\"> " + weapon[2] + "</span></sup></td><td>" + "{0:.12f}".format(weapon[3]) + "</td></tr>")

    return weaponString

def sortFloat(skns):
    floats = [skn[3] for skn in skns]
    return [s for (f,s) in sorted(zip(floats,skns))]

def convertKeyString(keys):
    keyList = sortKeys(keys)
    keyString = ""

    if len(keyList) != 0:
        keyString += "<tr><th>Keys</th>"
        keyString += ("<th>" + str(sum([keys[k] for k in keys])) + "</th></tr>")

        for key in keyList:
            keyString += ("<tr><td>" + key[0] + "</td><td>" + str(key[1]) + "</td></tr>")

    return keyString

def sortKeys(keys):
    keyList = [[key, keys[key]] for key in keys]
    counts = [c for (n,c) in keyList]
    return [k for (c,k) in sorted(zip(counts,keyList))[::-1]]
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80', threaded=True)
