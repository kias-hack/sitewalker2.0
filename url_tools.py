import re


class URL:
    def __init__(self, url: str):
        self.regex = r"(((^(?P<protocol>[\w]+))\:\/\/)(?P<domain>[a-zA-Z0-9а-яА-Я][" \
                     r"a-zA-Z0-9а-яА-Я\-\._]{1,63}))?(?P<path>[^?^#]+)?(?P<query>\?[^#]+)?(?P<hash>\#[\S]+)?$"

        self.url = url.strip()
        self.groups = {}
        self.query_params = {}
        self.is_invalid = False

        self.exec()

    def exec(self):
        if not self.url:
            self.is_invalid = True
            return

        match = re.match(self.regex, self.url)

        if not match:
            self.is_invalid = True
        else:
            self.is_invalid = False
            self.groups = re.match(self.regex, self.url).groupdict()

            if self.groups["query"]:
                # print(self.groups["query"][1:])
                self.query_params = dict([[param.split("=")[0], ""] if len(param.split("=")) != 2 else param.split("=")[:2] for param in self.groups["query"][1:].split("&")])


def url_filter(settings, src):
    url = URL(src)

    if url.is_invalid:
        return False

    if "mailto" in src or "javascript" in src or "tel" in src:
        return False

    for ext in [".jpg", ".png", ".svg", "jpeg", "pdf", "rar", "zip"]:
        if ext in src.lower():
            return False

    if url.groups["path"]:
        for path in settings["exclude_path"]:
            if path.startswith("/"):
                if url.groups["path"].startswith(path):
                    return False
            else:
                if path in url.groups["path"]:
                    return False

    for param in settings["exclude_search_params"]:
        if param in url.query_params.keys():
            return False

    if settings["ignore_hash"] and url.groups["hash"] and len(url.groups["hash"]) > 0:
        return False

    if url.groups["domain"] and settings["domain"] != url.groups["domain"]:
        return False

    if url.groups["protocol"] and url.groups["protocol"] not in ["http", "https"]:
        return False

    return True

def link_filter(settings):
    return lambda link: url_filter(settings, link.get("href") if link.get("href") is not None else "")
