#!/usr/bin/env python3
import json
import re
import urllib
import urllib.parse
import urllib.request


def latest():
    url = 'https://api.github.com/repos/replicate/cog-runtime/releases/latest'
    content = urllib.request.urlopen(url).read()
    blob = json.loads(content)
    whl = blob['assets'][0]['browser_download_url']
    m = re.match(r'.*/coglet-(?P<version>[^-]+)-.*\.whl', whl)
    print(m.group('version'))


if __name__ == '__main__':
    latest()
