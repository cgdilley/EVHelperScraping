
import Utils

from lxml.html import HtmlElement as Element
import httpx

import os
from typing import Iterable


HTML_DIR = "../data/html"
DEX_FILE = "full_dex_za.html"
DEX_DIRECTORY = "pokemon"


def main():

    root = load_dex_file()
    links = list(scrape_dex_links(root))

    for name, link in links:
        download_dex_link(name, link, ignore_already_downloaded=False)


#


def load_dex_file() -> Element:
    return Utils.parse_html(os.path.join(HTML_DIR, DEX_FILE))


#


def scrape_dex_links(root: Element) -> Iterable[tuple[str, str]]:
    main_block = root.find(".//main")
    dexes = main_block.findall(".//div[@class='infocard-list infocard-list-pkmn-lg']")

    # dex_body = dex_table.find("tbody")
    for dex in dexes:
        for row in (row for row in dex if row.tag == "div"):
            cols = row.findall("span")
            if len(cols) < 2:
                continue
            link_tag = cols[1].find("a")
            yield link_tag.text, f"https://pokemondb.net{link_tag.get('href')}"


def download_dex_link(name: str, link: str, ignore_already_downloaded: bool = False):
    clean_name = name.replace("♂", "-m").replace("♀", "-f").replace(":", "")

    filename = os.path.join(HTML_DIR, DEX_DIRECTORY, f"{clean_name}.html")
    if ignore_already_downloaded and os.path.exists(filename):
        return

    response = httpx.get(url=link, timeout=15)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(name)


#


#


#


if __name__ == "__main__":
    main()
