from EVHelperCore.Objects import *
from EVHelperCore.Utils import FormatUtils, ShowdownUtils
from EVHelperCore.Utils.DictUtils import unique_by

import Utils

from lxml.html import XHTMLParser, fromstring, Element, tostring

import re
import json
import os
from typing import Collection, Tuple, Iterable, Optional, Union

HTML_DIR = "../data/html"
DEX_DIRECTORY = "pokemon"
OUTPUT_FILE = "../data/json/dex.json"


def main():
    pages = os.listdir(os.path.join(HTML_DIR, DEX_DIRECTORY))

    pokemon = (pok for page in pages for pok in scrape_page(os.path.join(HTML_DIR, DEX_DIRECTORY, page)) if pok)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pok in pokemon:
            print(pok)
            f.write(json.dumps(pok.to_json(), ensure_ascii=False) + "\n")


def scrape_page(file: str) -> Iterable[PokemonData]:
    root = Utils.parse_html(file)

    name = root.find(".//*[@id='main']").find("h1").text

    tab_list = root.find(".//*[@class='tabs-tab-list']")
    tabs = [(a.text, a.get("href")[1:]) for a in tab_list.findall("a")]

    default = parse_pokemon_from_tab(root=root,
                                     tab_id=tabs[0][1],
                                     tab_name=tabs[0][0],
                                     pokemon_name=name)
    yield default

    for tab in tabs[1:]:
        yield parse_pokemon_from_tab(root=root,
                                     tab_id=tab[1],
                                     tab_name=tab[0],
                                     pokemon_name=name,
                                     default=default)


def parse_pokemon_from_tab(root: Element, tab_id: str, tab_name: str, pokemon_name: str,
                           default: Optional[PokemonData] = None) -> Optional[PokemonData]:
    args = {
        "move_list": MoveList(),
        "misc_info": MiscInfo(),
        "dex_entries": DexEntryCollection()
    }

    #

    #
    # Figure out name and variant

    variant_str = tab_name.replace(pokemon_name, "").replace("  ", " ").strip()

    variant_str_split = variant_str.split(" ")
    first_word = variant_str_split[0]
    remaining_words = " ".join(variant_str_split[1:])
    if Region.is_region_descriptor(first_word):
        region = Region.parse_descriptor(first_word)
        variant_name = PrefixVariantName(first_word, {})
        variant_str = remaining_words.strip()
    else:
        region = Region.NONE
        variant_name = None

    if variant_str == "":
        args["variant"] = Variant(region=region)
    elif variant_str in ["Male", "Female"]:
        args["variant"] = Variant(gender=Gender(variant_str.upper()), region=region)
        variant_name = _merge_variant_names(variant_name, SuffixVariantName(variant_str, {}))
    elif variant_str.startswith("Mega"):
        mega_type = MegaType.X if variant_str.endswith("X") else MegaType.Y if variant_str.endswith("Y") else \
            MegaType.NORMAL
        args["variant"] = Variant(mega_type=mega_type, region=region)
        if mega_type == MegaType.NORMAL:
            variant_name = _merge_variant_names(variant_name, PrefixVariantName("Mega", {}))
        else:
            variant_name = _merge_variant_names(variant_name, CircumfixVariantName("Mega", variant_str[-1], {}, {}))
    elif variant_str == "Primal":
        args["variant"] = Variant(form="Primal", region=region)
        variant_name = _merge_variant_names(variant_name, PrefixVariantName("Primal", {}))
    else:
        args["variant"] = Variant(form=variant_str, region=region)
        if pokemon_name in ["Kyurem", "Hoopa"]:
            variant_name = _merge_variant_names(variant_name, SuffixVariantName(variant_str, {}, comma=False))
        elif pokemon_name == "Rotom":
            variant_name = _merge_variant_names(variant_name, SuffixVariantName(variant_str, {}, spacer="-"))
        elif variant_str in ["Partner", "Own Tempo"] or pokemon_name in ["Necrozma"]:
            variant_name = _merge_variant_names(variant_name, PrefixVariantName(variant_str, {}))
        elif variant_str == "Ash-":
            variant_name = _merge_variant_names(variant_name, PrefixVariantName("Ash", {}, spacer="-"))
        else:
            variant_name = _merge_variant_names(variant_name, SuffixVariantName(variant_str, {}, comma=True))
    args["name"] = Name(pokemon_name, {}, variant_name=variant_name)

    #

    #
    # Get typing, abilities, dex entries, and misc_info

    tab_div = root.find(f".//*[@id='{tab_id}']")

    tables = tab_div.findall(".//*[@class='vitals-table']")
    pokedex_data = tables[0].find("tbody")
    training = tables[1].find("tbody")

    for row in pokedex_data:
        header = row.find("th").text

        #

        if header == "Type":
            types = [Type(a.text.upper()) for a in row.find("td").findall("a")]
            if len(types) == 0:
                return None
            args["typing"] = Typing(*types)

        #

        elif header == "Abilities":
            abilities = dict()
            col = row.find("td")
            for span in col.findall("span") + col.findall("small"):
                ability_link = span.find("a")
                if ability_link.tail == " (hidden ability)":
                    abilities["hidden_ability"] = Ability(ability_link.text)
                elif span.text == "1. ":
                    abilities["primary_ability"] = Ability(ability_link.text)
                elif span.text == "2. ":
                    abilities["secondary_ability"] = Ability(ability_link.text)
            if len(abilities) == 0:
                if default:
                    args["abilities"] = default.abilities
                else:
                    return None
            else:
                args["abilities"] = AbilityList(**abilities)

        #

        elif header == "National №":
            col = row.find("td").find("strong")
            args["dex_entries"].add_entry(DexEntry(Dex.NATIONAL, int(col.text)))

        #

        elif header == "Local №":
            col = row.find("td")
            if not col.text:
                continue
            curr_num = int(col.text)
            for tag in col:
                if tag.tag == "br":
                    curr_num = int(tag.tail) if tag.tail else None
                else:
                    args["dex_entries"].add_entry(DexEntry(Dex(tag.text[1:-1]), curr_num))

    for row in training:
        header = row.find("th").text

        if header == "EV yield":
            col = row.find("td")
            if not col.text.strip():
                continue
            stats = (s.strip() for s in col.text.split(","))

            ev_yield = EVYield(*(({
                                      "Attack": Stat.ATTACK, "Defense": Stat.DEFENSE, "Special Attack": Stat.SP_ATTACK,
                                      "Special Defense": Stat.SP_DEFENSE, "Speed": Stat.SPEED, "HP": Stat.HP
                                  }[stat], int(value)) for stat_info in stats for value, stat in
                                 (stat_info.split(" ", maxsplit=1),)))
            args["misc_info"].ev_yield = ev_yield

    #

    #
    # Get evolution line

    if args["name"].name in ["Nincada", "Ninjask", "Shedinja"]:
        args["misc_info"].evolution_line = \
            EvolutionLine("NINCADA",
                          (Evolution("NINCADA", "NINJASK", LevelUpEvolutionType(20)),
                           EvolutionLine("NINJASK")),
                          (Evolution("NINCADA", "SHEDINJA", UnknownEvolutionType()),
                           EvolutionLine("SHEDINJA")))
    else:
        evo_lines = []

        for evo_line_info in root.findall(f".//div[@class='infocard-list-evo']"):
            evo_line = _scrape_evolution_line(evo_line_info)
            if isinstance(evo_line, EvolutionLine):
                evo_lines.append(evo_line)

        evo_lines = list(EvolutionLine.merge(*evo_lines))

        formatted_name = FormatUtils.format_name_as_id(args["name"], args["variant"], ignore_mega=True)
        evo_lines = [evl for evl in evo_lines
                     if formatted_name in evl.get_all_pokemon_ids_in_line()]
        if len(evo_lines) == 1:
            args["misc_info"].evolution_line = evo_lines[0]
        elif len(evo_lines) > 1:
            print("MULTIPLE EVO LINES FOUND")

    #

    #
    # Get stats

    stats_div = tab_div.find(".//*[@id='dex-stats']...")
    stats_table = stats_div.find(".//table")
    if stats_table is None:
        return None
    stats_table = stats_table.find("tbody")

    stats = dict()
    for row in stats_table:
        header = row.find("th").text
        value = int(row.find("td").text)
        stat = {
            "HP": "hp",
            "Attack": "attack",
            "Defense": "defense",
            "Sp. Atk": "special_attack",
            "Sp. Def": "special_defense",
            "Speed": "speed"
        }[header]
        stats[stat] = value
    args["stats"] = BaseStats(**stats)

    #

    return PokemonData(**args)


def _scrape_evolution_line(evo_line_info: Element) -> Union[EvolutionLine, dict]:
    def is_class(elem: Element, c: str) -> bool:
        # return c in elem.classes
        return "class" in elem.attrib and c in elem.attrib["class"].strip().split(" ")

    evo_scraped = {"evolutions": []}
    for pokemon_info in reversed(evo_line_info):
        if pokemon_info.tag == "div" and is_class(pokemon_info, "infocard"):
            if "name" in evo_scraped:
                evo_scraped = {"evolutions": [evo_scraped]}
            for span in pokemon_info.findall("span"):
                if not is_class(span, "infocard-lg-data"):
                    continue
                for info in span:
                    if info.tag == "a" and is_class(info, "ent-name"):
                        evo_scraped["name"] = info.text
                    elif info.tag == "small" and "name" in evo_scraped and info.text:
                        if evo_scraped["name"] in info.text:
                            evo_scraped["name"] = info.text
                        else:
                            split_ = info.text.split(" ")
                            if split_[0] in ["Alolan", "Galarian"]:
                                evo_scraped["name"] = split_[0] + " " + evo_scraped["name"]
                                if len(split_) > 1:
                                    evo_scraped["name"] += " " + " ".join(split_[1:])
                            else:
                                evo_scraped["name"] += " " + info.text
                if "name" not in evo_scraped:
                    print("FAILED TO FIND EVO NAME")
                    continue
                evo_scraped["name"] = FormatUtils.format_name_as_id(Name(evo_scraped["name"].strip(), {}))
        elif pokemon_info.tag == "span" and is_class(pokemon_info, "infocard-arrow"):
            evo_text = pokemon_info.find("small").text
            m = re.match(r"\(Level (\d+)\)", evo_text)
            evo_scraped["evo"] = LevelUpEvolutionType(level=int(m.group(1))) if m else UnknownEvolutionType()
        elif pokemon_info.tag == "span" and is_class(pokemon_info, "infocard-evo-split"):
            evo_scraped = {"evolutions": []}
            for span in pokemon_info.findall("span"):
                div = span.find("div")
                evo_line = _scrape_evolution_line(div)
                evo_scraped["evolutions"].append(evo_line)
            # evo_scraped = {"evolutions": [evo_line for evo_line in (_scrape_evolution_line(span.find("div"))
            #                                                         for span in pokemon_info.findall("span"))]}

    def convert_scraped_to_line(scraped: dict) -> EvolutionLine:
        return EvolutionLine(scraped["name"],
                             *(
                                 (Evolution(scraped["name"], evo["name"], evo["evo"]),
                                  convert_scraped_to_line(evo))
                                 for evo in scraped["evolutions"]
                             ))

    if "evo" in evo_scraped:
        return evo_scraped

    return convert_scraped_to_line(evo_scraped)


def _merge_variant_names(name1: Optional[VariantName], name2: Optional[VariantName]) -> VariantName:
    if name2 is None:
        return name1
    if name1 is None:
        return name2

    if isinstance(name1, PrefixVariantName):
        if isinstance(name2, PrefixVariantName):
            return PrefixVariantName(f"{name1.name} {name2.name}",
                                     {lang: f"{loc} {name2.localized_name(lang)}"
                                      for lang, loc in name1._localized_names.items()
                                      if lang in name2._localized_names},
                                     spacer=name2.spacer)
        elif isinstance(name2, SuffixVariantName):
            return CircumfixVariantName(name1.name, name2.name, name1._localized_names, name2._localized_names,
                                        suffix_comma=name2.comma == ",",
                                        prefix_spacer=name1.spacer,
                                        suffix_spacer=name2.spacer)
        elif isinstance(name2, CircumfixVariantName):
            return CircumfixVariantName(f"{name1.name} {name2._default_prefix}", name2._default_suffix,
                                        {lang: f"{loc} {name2._localized_prefix[lang]}"
                                         for lang, loc in name1._localized_names.items()
                                         if lang in name2._localized_prefix},
                                        name2._localized_suffix,
                                        suffix_comma=name2.suffix_comma == ",",
                                        prefix_spacer=name2.prefix_spacer,
                                        suffix_spacer=name2.suffix_spacer)

    elif isinstance(name1, SuffixVariantName):
        if isinstance(name2, PrefixVariantName):
            return CircumfixVariantName(name2.name, name1.name, name2._localized_names, name1._localized_names,
                                        suffix_comma=name1.comma == ",",
                                        prefix_spacer=name2.spacer)
        elif isinstance(name2, SuffixVariantName):
            return SuffixVariantName(f"{name1.name}{',' if name2.comma else ''} {name2.name}",
                                     {lang: f"{loc}{',' if name2.comma else ''} {name2.localized_name(lang)}"
                                      for lang, loc in name1._localized_names.items()
                                      if lang in name2._localized_names},
                                     comma=name1.comma == ",",
                                     spacer=name1.spacer)
        elif isinstance(name2, CircumfixVariantName):
            return CircumfixVariantName(name2._default_prefix, f"{name1.name} {name2._default_suffix}",
                                        name2._localized_prefix,
                                        {lang: f"{loc} {name2._localized_suffix[lang]}"
                                         for lang, loc in name1._localized_names.items()
                                         if lang in name2._localized_suffix},
                                        suffix_comma=name1.comma == ",",
                                        prefix_spacer=name2.prefix_spacer,
                                        suffix_spacer=name1.spacer)
    elif isinstance(name1, CircumfixVariantName):
        if isinstance(name2, PrefixVariantName):
            return CircumfixVariantName(f"{name1._default_prefix} {name2.name}",
                                        name1._default_suffix,
                                        {lang: f"{loc} {name2.localized_name(lang)}"
                                         for lang, loc in name1._localized_prefix.items()
                                         if lang in name2._localized_names},
                                        name1._localized_suffix,
                                        suffix_comma=name1.suffix_comma == ",",
                                        prefix_spacer=name2.spacer,
                                        suffix_spacer=name1.suffix_spacer)
        elif isinstance(name2, SuffixVariantName):
            return CircumfixVariantName(name1._default_prefix,
                                        f"{name1._default_suffix} {name2.name}",
                                        name1._localized_prefix,
                                        {lang: f"{loc} {name2.localized_name(lang)}"
                                         for lang, loc in name1._localized_suffix.items()
                                         if lang in name2._localized_names},
                                        suffix_comma=name2.comma == ",",
                                        prefix_spacer=name1.prefix_spacer,
                                        suffix_spacer=name1.suffix_spacer)
        elif isinstance(name2, CircumfixVariantName):
            return CircumfixVariantName(f"{name1._default_prefix} {name2._default_prefix}",
                                        f"{name2._default_suffix} {name1._default_suffix}",
                                        {lang: f"{loc} {name2._localized_prefix[lang]}"
                                         for lang, loc in name1._localized_prefix.items()
                                         if lang in name2._localized_prefix},
                                        {lang: f"{name2._localized_suffix[lang]} {loc}"
                                         for lang, loc in name1._localized_suffix.items()
                                         if lang in name2._localized_suffix},
                                        prefix_comma=name2.prefix_comma == ",",
                                        suffix_comma=name2.suffix_comma == ",",
                                        prefix_spacer=name2.prefix_spacer,
                                        suffix_spacer=name2.suffix_spacer)
    return name1


#


#


#


if __name__ == "__main__":
    main()
