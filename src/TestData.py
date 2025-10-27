from EVHelperCore import *

import json

DEX_FILE = "../data/json/dex.json"


def main():
    with open(DEX_FILE, "r", encoding="utf-8") as f:
        data = PokemonDataMap(*(PokemonData.from_json(json.loads(line)) for line in f.readlines() if line))

        for forms in data.nat_dex_map.values():
            if any(d.variant.is_mega() for d in forms):
                try:
                    base = next(f for f in forms if f.variant.is_base_variant())
                except StopIteration:
                    continue
                mega = next(f for f in forms if f.variant.is_mega())

                if base.typing != mega.typing:
                    print(format_showdown_name(base.name.base_name(), base.variant) + "  --  " +
                          str(base.typing) + "   ===>   " + format_showdown_name(mega.name.base_name(), mega.variant) + "  --  " +
                          str(mega.typing))



#


#


#


if __name__ == "__main__":
    main()
