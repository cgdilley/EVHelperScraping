
from EVHelperCore.Objects import *
from EVHelperCore.Utils.ShowdownUtils import format_showdown_name

import os
import json


DEX_FILE = "../data/json/dex.json"


def main():
    with open(DEX_FILE, "r", encoding="utf-8") as f:
        data = PokemonDataMap(*(PokemonData.from_json(json.loads(line)) for line in f.readlines() if line))

    for d in data.ev_yield(Stat.SP_DEFENSE, 1, strict=True):
        print(format_showdown_name(d.name.base_name(), d.variant))


#


#


#


if __name__ == "__main__":
    main()
