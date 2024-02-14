from typing import List

from tools import load_settings, store_process, store_processed, restore_process, restore_processed, URLEntry
from os.path import exists
from os import unlink
from url_tools import link_filter, url_filter, URL
import atexit


def exit_handler():
    if exists(settings["output_filename"] + ".process.csv"):
        unlink(settings["output_filename"] + ".process.csv")
    if exists(settings["output_filename"] + ".processed.csv"):
        unlink(settings["output_filename"] + ".processed.csv")

    store_process(settings["output_filename"] + ".process.csv", unknown_pages)
    store_processed(settings["output_filename"] + ".processed.csv", known_pages)


atexit.register(exit_handler)

settings = load_settings(open("./setting.json"))

unknown_pages: List[URLEntry] = []
known_pages = []

if exists(settings["output_filename"] + ".process.csv"):
    unknown_pages = restore_process(settings["output_filename"] + ".process.csv")

if exists(settings["output_filename"] + ".processed.csv"):
    known_pages = restore_processed(settings["output_filename"] + ".processed.csv")

if len(unknown_pages) == 0:
    address = "{}://{}".format(settings['protocol'], settings['domain'])

    unknown_pages.append(URLEntry(address))

while len(unknown_pages):
    url_entry = unknown_pages.pop()

    if not url_filter(settings, url_entry.url):
        continue

    if url_entry.url in known_pages:
        continue

    url_entry.fetch()
    url_entry.log(settings["output_filename"] + ".csv")

    print("fetch {} [{}] / {}".format(url_entry.url, url_entry.status_code, len(unknown_pages)))

    known_pages.append(url_entry.url)

    links, source_url = url_entry.get_links()

    links = filter(link_filter(settings), links)

    for link in links:
        href = link.get("href")
        local_link = URL(href if href is not None else "")

        if local_link.is_invalid:
            continue

        if local_link.groups["domain"] is not None and local_link.groups["domain"] != settings["domain"]:
            continue

        norm_link = ("{}://{}{}".format(settings["protocol"], settings["domain"], local_link.groups["path"])).strip()

        next = False
        for ue in unknown_pages:
            if norm_link == ue.url:
                next = True

        if next or norm_link in known_pages:
            entry = URLEntry(norm_link, source_url, link.text)
            entry.log(settings["output_filename"] + ".csv")
            continue

        unknown_pages.append(URLEntry(norm_link, source_url, link.text))
