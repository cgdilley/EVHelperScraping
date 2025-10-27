from SprelfPkmn import *
import Utils

import json
import os
from typing import Iterable

HTML_DIR = "../data/html"
DEX_DIRECTORY = "moves"
OUTPUT_FILE = "../data/json/moves.json"


def main():
    pages = os.listdir(os.path.join(HTML_DIR, DEX_DIRECTORY))

    moves = (move for page in pages for move in scrape_page(os.path.join(HTML_DIR, DEX_DIRECTORY, page)) if move)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for move in moves:
            print(move)
            f.write(json.dumps(move.to_json(), ensure_ascii=False) + "\n")


def scrape_page(file: str) -> Iterable[Move]:
    root = Utils.parse_html(file)

    content = root.find(".//*[@id='main']")
    name = content.find("h1").text.strip()

    vitals = content.find(".//*[@class='vitals-table']")

    values = [elem for elem in vitals.iterdescendants() if elem.tag == "td"]
    category = "".join(values[1].itertext()).strip()

    description = None
    for elem in content.iterdescendants():
        if elem.tag == "h2" and elem.text == "Effects":
            description = ""
        elif description is not None:
            if elem.tag == "p":
                if description:
                    description += "\n"
                description += "".join(elem.itertext())
            elif elem.tag == "h3":
                break
    else:
        description = ""

    if values[3].attrib.get("class", None) == "num-infinity":
        accuracy = 0
    elif values[3].text == "—":
        accuracy = None
    else:
        accuracy = int(values[3].text)

    if category == "Status":
        yield StatusMove(name=name,
                         type=Type[values[0].find("a").text.upper()],
                         max_pp=values[4].text.strip(),
                         accuracy=accuracy,
                         description=description,
                         properties=MoveProperties.CONTACT if values[5].text == "Yes" else MoveProperties.NONE)
    else:
        yield DamagingMove(name=name,
                           type=Type[values[0].find("a").text.upper()],
                           max_pp=values[4].text.strip(),
                           accuracy=accuracy,
                           description=description,
                           base_power=int(values[2].text) if values[2].text != "—" else 0,
                           offense_stat=Stat.SP_ATTACK if category == "Special" else Stat.ATTACK,
                           defense_stat=Stat.SP_DEFENSE if category == "Special" else Stat.DEFENSE,
                           properties=MoveProperties.CONTACT if values[5].text == "Yes" else MoveProperties.NONE)


#


#


#


if __name__ == "__main__":
    main()
