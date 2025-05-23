#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib
import urllib.request
from http import HTTPStatus

MONOBASE_PREFIX = os.environ.get('MONOBASE_PREFIX', '/srv/r8/monobase')
PGET_BIN = os.environ.get('PGET_BIN', os.path.join(MONOBASE_PREFIX, 'bin/pget-bin'))
KNOWN_WEIGHTS_DIR = os.environ.get('KNOWN_WEIGHTS_DIR', '')

parser = argparse.ArgumentParser('refresh_files')
parser.add_argument('-f', '--file-stats-url', type=str)
parser.add_argument('-u', '--upstream-url', type=str)


def find_pget_exe() -> str:
    # PGET_BIN is executable
    if os.path.isfile(PGET_BIN) and os.access(PGET_BIN, os.X_OK):
        return PGET_BIN
    # Look for real executable in PATH
    for p in os.environ['PATH'].split(os.pathsep):
        f = shutil.which('pget', path=p)
        if f is not None and f != __file__:
            return f
    print('Cannot find pget executable', file=sys.stderr)
    sys.exit(1)


def main(url, upstream) -> None:
    if not url:
        print('Misconfigured files URL, exiting')
        sys.exit(1)

    try:
        req = urllib.request.Request(url, method='GET')
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        print(f'Failed request to {url}: {e.read().decode()}; exiting')
        sys.exit(1)

    if resp.status != HTTPStatus.OK:
        print(f'Failed request to {url}: {resp.read().decode()}; exiting')
        sys.exit(1)

    # The expectation for response from the file-stats-url is that
    # it is a GET request that returns a list of files, like
    # {
    #   "files": [
    #     "URL1",
    #     "URL2",
    #     "...",
    #   ]
    # }
    body = json.loads(resp.read().decode())
    if 'files' not in body:
        print(f'Malformatted response: {body}; exiting')
        sys.exit(1)

    p = find_pget_exe()
    # pget each of the files into the new directory
    for file in body['files']:
        h = hashlib.sha256(file.encode())
        # If we have an upstream, make the URL <upstream>/<file> but strip http(s)://
        # from the <file> URL
        if upstream:
            if file.startswith('http'):
                file = re.sub(r'https?:\\', '', file)
            file = f'{upstream}/{file}'
        try:
            subprocess.run([p, file, os.path.join('/tmp', h.hexdigest())])
            shutil.move(
                os.path.join('/tmp', h.hexdigest()),
                os.path.join(KNOWN_WEIGHTS_DIR, h.hexdigest()),
            )
        except Exception as e:
            print(f'Error downloading {file}: {e}')
            # Continue on anyways to get the rest of the files


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.file_stats_url, args.upstream_url)
