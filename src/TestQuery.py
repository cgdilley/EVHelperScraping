
from EVHelperCore.Objects import *
from EVHelperCore.Utils.ShowdownUtils import format_showdown_name

import os
import json


DEX_FILE = "../data/json/dex.json"


def main():
    with open(DEX_FILE, "r", encoding="utf-8") as f:
        data = PokemonDataMap(*(PokemonData.from_json(json.loads(line)) for line in f.readlines() if line))

    while True:
        text = input("\nName? ")
        if not text:
            break
        matches = data.name(text)
        for m in matches:
            num = m.dex_entries.get_dex_num(Dex.GEN_8_DLC2)
            print(f"{m.name_id}: {num if num else 'None'} ({m.dex_entries.get_dex_num(Dex.NATIONAL)})")
        # print("\n".join(json.dumps(m.to_json(), indent=2, ensure_ascii=False) for m in matches))


#


#


#


if __name__ == "__main__":
    main()
