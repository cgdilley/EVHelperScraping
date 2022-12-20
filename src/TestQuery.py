
from EVHelperCore.Objects import *
from EVHelperCore.Utils.ShowdownUtils import format_showdown_name

import os
import json


DEX_FILE = "../data/json/dex.json"


def main():
    with open(DEX_FILE, "r", encoding="utf-8") as f:
        data = PokemonDataMap(*(PokemonData.from_json(json.loads(line)) for line in f.readlines() if line))

    grouping = dict()
    for mon in data:
        if Dex.GEN_9 in mon.dex_entries:
            if len(mon.misc_info.ev_yield.yields) == 1:
                stat = list(mon.misc_info.ev_yield.yields.keys())[0]
                if stat in grouping:
                    grouping[stat].append(mon)
                else:
                    grouping[stat] = [mon]

    for stat, mons in grouping.items():
        print(f"{stat}:\n-----------------")
        for mon in sorted(mons, key=lambda m: sum(m.misc_info.ev_yield.yields.values()), reverse=True):
            print(f"{mon.name_id} : {mon.misc_info.ev_yield}")
        print()

    # while True:
    #     text = input("\nName? ")
    #     if not text:
    #         break
    #     matches = data.name(text)
    #     for m in matches:
    #         num = m.dex_entries.get_dex_num(Dex.GEN_8_DLC2)
    #         print(f"{m.name_id}: {num if num else 'None'} ({m.dex_entries.get_dex_num(Dex.NATIONAL)})")
        # print("\n".join(json.dumps(m.to_json(), indent=2, ensure_ascii=False) for m in matches))


#


#


#


if __name__ == "__main__":
    main()
