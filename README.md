# csgoSkinStatistics

A very simple site designed to hit csgo's game coordinator and return information about csgo items.

### Requirements

This repository has 3 external dependencies. These are:
+ Flask
+ ValvePython/steam https://github.com/ValvePython/steam
+ ValvePython/csgo https://github.com/ValvePython/csgo

### Installation and Setup

After cloning this repository, simply run the skinstats module with Python 3. If you have set the environment variables `steam_user` and `steam_pass`, it will use those. Otherwise, you will be prompted to input those manually. The page will be on localhost:5000.

### Todo (recent)
- [x] fix items with apostrophe in name (should come along with previous todo and making response easier to parse)
- [x] show if a weapon is stattrak
- [x] switch to actually using a database rather than a flat text file
- [ ] more servers
- [ ] load balancing
