#!/usr/bin/env python3

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from http import HTTPStatus

import requests

parser = argparse.ArgumentParser('refresh_files')
parser.add_argument('-f', '--file-stats-url', type=str)
parser.add_argument('-u', '--upstream-url', type=str)
parser.add_argument('-p', '--parent-dir', type=str)

KNOWN_WEIGHTS_DIR_ENV_VAR = 'KNOWN_WEIGHTS_DIR'


def find_pget_exe() -> str:
    # Look for real executable in PATH
    for p in os.environ['PATH'].split(os.pathsep):
        f = shutil.which('pget', path=p)
        if f is not None and f != __file__:
            return f
    print('Cannot find pget executable', file=sys.stderr)
    sys.exit(1)


def main(url, upstream, parent_dir) -> None:
    if not url:
        print('Misconfigured files URL, exiting')
        sys.exit(1)
    resp = requests.get(url)
    if resp.status_code != HTTPStatus.OK:
        print(f'Failed request to {url}: {resp.text}; exiting')
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
    body = resp.json()
    if 'files' not in body:
        print(f'Malformatted response: {body}; exiting')
        sys.exit(1)

    old_dir = os.environ.get(KNOWN_WEIGHTS_DIR_ENV_VAR, '')

    # Create a new directory to be the known_files_directory
    now = datetime.now()
    m = hashlib.sha256(now.strftime('%Y-%m-%d-%H:%M:%S').encode())
    new_dir = os.path.join(parent_dir, m.hexdigest())
    os.makedirs(new_dir)
    p = find_pget_exe()
    # pget each of the files into the new directory
    for file in body['files']:
        h = hashlib.sha256(file.encode())
        old_path = os.path.join(old_dir, h.hexdigest())
        new_path = os.path.join(new_dir, h.hexdigest())
        # Copy instead of pget if the old path already exists
        if os.path.exists(old_path):
            shutil.copy(old_path, new_path)
        else:
            # If we have an upstream, make the URL <upstream>/<file> but strip http(s)://
            # from the <file> URL
            if upstream:
                if file.startswith('http'):
                    file = re.sub(r'https?:\\', '', file)
                file = f'{upstream}/{file}'
            subprocess.run([p, file, new_path])

    # Switch the old env var
    os.environ[KNOWN_WEIGHTS_DIR_ENV_VAR] = new_dir

    # Remove old cache dir after 10 minutes to make sure nothing is reading from
    # those files anymore
    if old_dir:
        time.sleep(600)
        os.rmdir(old_dir)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.file_stats_url, args.upstream_url, args.parent_dir)
