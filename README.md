# csgoSkinStatistics

A very simple site designed to hit csgo's game coordinator and return information about csgo items.

### Requirements

This repository has 3 external dependencies. These are:
+ Flask
+ ValvePython/steam https://github.com/ValvePython/steam
+ ValvePython/csgo https://github.com/ValvePython/csgo

### Installation and Setup

After cloning this repository, simply run the skinstats module with Python 3. If you have set the environment variables `steam_user` and `steam_pass`, it will use those. Otherwise, you will be prompted to input those manuallyi. The page will be on localhost:5000.

Run skinstats.py with Python 3 to start the application. The page will be on localhost:5000.

#### TODO

+ database support
+ remove json dependency
+ more i'm likely forgetting...
