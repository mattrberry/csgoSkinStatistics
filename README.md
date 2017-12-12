# csgoSkinStatistics

A very simple site designed to hit csgo's game coordinator and return information about csgo items.

### Requirements

This repository has 3 external dependencies. These are:
+ Flask
+ ValvePython/steam https://github.com/ValvePython/steam
+ ValvePython/csgo https://github.com/ValvePython/csgo

### Installation and Setup

After cloning this repository, simply run the skinstats module with Python 3. If you have set the environment variables `steam_user` and `steam_pass`, it will use those. Otherwise, you will be prompted to input those manually. The page will be on localhost:5000.

### API

Endpoint: https://skinstats.io/api

#### Usage

###### Pre-Parsed Inspect Link Elements (preferred)

|Parameter|Description                                   |
|---------|----------------------------------------------|
|s        |Required (used if item from inventory, else 0)|
|a        |Required (inspect link 'a' parameter)         |
|d        |Required (inspect link 'd' parameter)         |
|m        |Required (used if item from market, else 0)   |

Example Inventory Item

`https://skinstats.io/api?s=76561198261551396&a=12256887280&d=2776544801323831695&m=0`

Example Market Item

`https://skinstats.io/api?m=563330426657599553&a=6710760926&d=9406593057029549017&s=0`

###### Full Inspect URL

|Parameter|Description                         |
|---------|------------------------------------|
|url      |Required (full inspect link of item)|

Example Inventory Item

`https://skinstats.io/api?url=steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198261551396A12256887280D2776544801323831695`

Example Market Item

`https://skinstats.io/api?url=steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M625254122282020305A6760346663D30614827701953021`

#### Response

|Attribute |Type   |Description                                    |
|----------|-------|-----------------------------------------------|
|itemid    |integer|Item ID                                        |
|defindex  |integer|Weapon ID                                      |
|paintindex|integer|Numerical ID for the skin                      |
|rarity    |integer|Rarity value                                   |
|quality   |integer|Quality value                                  |
|paintwear |float  |Wear of the skin (0-1)                         |
|paintseed |integer|How the skin texture is placed                 |
|inventory |integer|Inventory ID                                   |
|origin    |integer|Origin of the weapon                           |
|stattrak  |integer|1 if stattrak, 0 if not                        |
|weapon    |string |Name of the weapon                             |
|skin      |string |Name of the skin                               |
|special   |string |Special attributes of the skin (i.e. "Phase 1")|

###### Errors

For right now, errors come in many non-conformed shapes and sizes. Hopefully you don't run into any, but if you do, make sure your input exactly matches the examples. If you still have problems, feel free to open an Issue on GitHub.

### Todo (recent)
- [x] fix items with apostrophe in name (should come along with previous todo and making response easier to parse)
- [x] show if a weapon is stattrak
- [x] switch to actually using a database rather than a flat text file
- [x] API
- [ ] more servers
- [ ] load balancing
