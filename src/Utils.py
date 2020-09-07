from lxml.html import XHTMLParser, fromstring, Element, tostring

import os


def parse_html(filename: str) -> Element:

    with open(filename, "r", encoding="utf-8") as f:
        text = f.read().replace("<br>", "<br/>")
    parser = XHTMLParser(recover=True, huge_tree=True)
    return fromstring(text, parser=parser)
