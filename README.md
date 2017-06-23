# csgoSkinStatistics

A very simple site designed to hit csgo's game coordinator and return information about csgo items.

### Requirements

This repository has 3 external dependencies. These are:
+ Flask
+ ValvePython/steam https://github.com/ValvePython/steam
+ ValvePython/csgo https://github.com/ValvePython/csgo

### Installation and Setup

After cloning this repository, create environment variables named 'steam_user' and 'steam_pass'. I imagine their contents are self explanatory.

Run skinstats.py with Python 3 to start the application. The page will be on localhost:5000.

#### TODO

+ database support rather than memoization
+ pep8
+ remove json dependency
+ more i'm likely forgetting...
