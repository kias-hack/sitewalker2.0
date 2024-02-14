import json
from urllib.parse import parse_qsl, urlunparse, urlparse, urljoin
import requests
from bs4 import BeautifulSoup as bs
import re

def joinurl(root: str, url: str, page: str):
    url = url.strip()
    page = page.strip()

    if url.startswith("http://") or url.startswith("https://"):
        return url

    if not len(page):
        page = root

    url = urlparse(url)
    url = url._replace(scheme="")
    url = url._replace(netloc="")
    url = url._replace(fragment="")

    filtered_params = []
    for query_pair in parse_qsl(url.query):
        name, val = query_pair

        val_url = urlparse(val)

        same = list(filter(lambda pair: pair[0] == name, parse_qsl(val_url.query)))

        if len(same) == 0:
            filtered_params.append("{}={}".format(name, val))

    url = url._replace(query="&".join(filtered_params))

    return urljoin(page, urlunparse(url))


def load_settings(path):
    return json.load(path)


class URLEntry:
    def __init__(self, url, source="", label=""):
        self.url = url
        self.source = source
        self.label = re.sub(r"[\W\D]", "", label)
        self.status_code = None
        self.redirect_url = None
        self.response = None
        self.fetched = False

    def fetch(self):
        response = requests.get(self.url)

        if len(response.history):
            self.status_code = response.history[0].status_code
            self.redirect_url = response.url
        else:
            self.status_code = response.status_code

        self.response = response
        self.fetched = True

    def get_links(self):
        if "text/html" in self.response.headers['Content-type']:
            return bs(self.response.text, "html.parser").findAll("a"), self.response.url

        return [], self.response.url

    def log(self, filename):
        with open(filename, "a", encoding="utf-8") as f:
            f.write("{};{};{};{};{}\n".format(self.url, str(self.status_code), self.redirect_url if self.redirect_url else "", self.source, self.label))

    def save(self, file):
        file.write("{};{};{}\n".format(self.url, self.source, self.label))


def store_process(filename, collection):
    with open(filename, "w+", encoding="utf-8") as file:
        for url in collection:
            url.save(file)


def store_processed(filename, collection):
    with open(filename, "w+", encoding="utf-8") as file:
        for url in collection:
            file.write("{}\n".format(url))


def restore_process(filename):
    collection = []
    set_collection = set()

    with open(filename, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if len(line):
                url, source, label = line.split(";")

                if url in set_collection:
                    continue

                set_collection.add(url)

                collection.append(URLEntry(url, source, label))

    return collection


def restore_processed(filename):
    collection = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if len(line.strip()):
                collection.append(line.strip())

    return collection
