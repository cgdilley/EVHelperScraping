from EVHelperCore import *

import json
import csv

DEX_FILE = "../data/json/dex.json"


def main():
    with open(DEX_FILE, "r", encoding="utf-8") as f:
        data = PokemonDataMap(*(PokemonData.from_json(json.loads(line)) for line in f.readlines() if line))

    with open("dex.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, ["Pokémon", "Final evo", "Type 1", "Type 2", "Ability 1", "Ability 2",
                                    "Hidden ability", "Dex #", "HP", "Attack", "Defense", "Sp.Attack", "Sp.Defense",
                                    "Speed"])
        writer.writeheader()
        # filtered_data = (d for d in data if not d.variant.is_mega())
        filtered_data = data
        sorted_data = sorted(filtered_data, key=lambda d: d.dex_entries.get_dex_num(Dex.NATIONAL))
        for d in sorted_data:
            final_ids = list(d.misc_info.evolution_line.get_final_evolution_ids()) \
                if d.misc_info.evolution_line is not None else []
            final_evo = d if d.name_id in final_ids else data.name_id(final_ids[0]) if len(final_ids) == 1 \
                else d if len(final_ids) == 0 else None

            def _capitalize(s: str) -> str:
                return s[0].upper() + s[1:].lower()

            writer.writerow({
                "Pokémon": format_showdown_name(d.name.base_name(), d.variant),
                "Final evo": format_showdown_name(final_evo.name.base_name(), final_evo.variant) if final_evo else "",
                "Type 1": _capitalize(d.typing.primary.name),
                "Type 2": _capitalize(d.typing.secondary.name) if d.typing.secondary
                else _capitalize(d.typing.primary.name),
                "Ability 1": d.abilities.primary,
                "Ability 2": d.abilities.secondary if d.abilities.secondary else "",
                "Hidden ability": d.abilities.hidden if d.abilities.hidden else "",
                "Dex #": d.dex_entries.get_dex_num(Dex.NATIONAL),
                "HP": d.stats.get_stat(Stat.HP),
                "Attack": d.stats.get_stat(Stat.ATTACK),
                "Defense": d.stats.get_stat(Stat.DEFENSE),
                "Sp.Attack": d.stats.get_stat(Stat.SP_ATTACK),
                "Sp.Defense": d.stats.get_stat(Stat.SP_DEFENSE),
                "Speed": d.stats.get_stat(Stat.SPEED)
            })


#


#


#


if __name__ == "__main__":
    main()
