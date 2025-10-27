from lxml.html import XHTMLParser, fromstring, Element, tostring

import os
import re

IMG_REGEX = re.compile(r"(<(source|img)[^>]+)>")


def parse_html(filename: str) -> Element:

    with open(filename, "r", encoding="utf-8") as f:
        text = f.read().replace("<br>", "<br/>").replace("<hr>", "hr/>")
        text = IMG_REGEX.sub("\1/>", text)
    parser = XHTMLParser(recover=True, huge_tree=True)
    return fromstring(text, parser=parser)
