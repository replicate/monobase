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
import urllib.parse
import urllib.request
from http import HTTPStatus

MONOBASE_PREFIX = os.environ.get('MONOBASE_PREFIX', '/srv/r8/monobase')
PGET_BIN = os.environ.get('PGET_BIN', os.path.join(MONOBASE_PREFIX, 'bin/pget-bin'))
PGET_KNOWN_WEIGHTS_DIR = os.environ.get('PGET_KNOWN_WEIGHTS_DIR', '')

parser = argparse.ArgumentParser('refresh_files')
parser.add_argument('-q', '--query-url', type=str, required=True)
parser.add_argument('-q', '--query-id', type=str, required=True)
parser.add_argument('-u', '--upstream-url', type=str)
parser.add_argument('-a', '--auth-token', type=str, required=True)
parser.add_argument('-m', '--max-size', type=int, required=True)


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


def main(query_url, query_id, upstream, auth_token, max_size) -> None:
    try:
        create_req = urllib.request.Request(
            query_url,
            method='POST',
            headers={'X-Honeycomb-Team': auth_token},
            data=urllib.parse.urlencode(
                {
                    'query_id': query_id,
                    'disable_series': True,
                    'disable_total_by_aggregate': True,
                    'disable_other_by_aggregate': True,
                }
            ).encode(),
        )
        create_resp = urllib.request.urlopen(create_req)

        create_body = json.loads(create_resp.read().decode())
        if 'id' not in create_body:
            print(f'Malformatted response from create endpoint: {create_body}; exiting')
            sys.exit(1)

        req = urllib.request.Request(
            urllib.parse.urljoin(query_url, create_body['id']),
            method='GET',
            headers={'X-Honeycomb-Team': auth_token},
        )
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        print(f'Failed request to {query_url}: {e.read().decode()}; exiting')
        sys.exit(1)

    if resp.status != HTTPStatus.OK:
        print(f'Failed request to {query_url}: {resp.read().decode()}; exiting')
        sys.exit(1)

    # The expectation for response from the file-stats-url is that
    # it is a GET request that returns a list of files, like
    # {
    #   "data": {
    #       "results": [
    #           {
    #               "cache.request.resolved_url": "URL1",
    #           },
    #           {
    #               "cache.request.resolved_url": "URL2",
    #           },
    #           ...,
    #       ],
    #   }
    # }
    body = json.loads(resp.read().decode())
    results = body.get('data', {}).get('results', [])
    if len(results) == 0:
        print(f'Malformatted response: {body}; exiting')
        sys.exit(1)

    file_set = set([])
    total_size = 0

    # Parse results to figure out what files to download
    for result in results:
        data = result.get('data', {})
        if 'cache.request.resolved_url' not in data:
            print(f'Malformatted result: {result}; continuing')
            continue
        file = data['cache.request.resolved_url']
        h = hashlib.sha256(file.encode())
        file_set.add(h.hexdigest())

        # Check we won't violate the total size by downloading this file
        if 'cache.response.object_size' not in data:
            print(f'Malformatted result: {result}; continuing')
            continue
        size = data['cache.response.object_size']
        if (total_size + size) > max_size:
            print(f'Downloading file would be violate size limit, skipping file {file}')
            continue
        total_size += size

    # Delete files that should no longer be here so we keep the directory clean
    for file in os.listdir(PGET_KNOWN_WEIGHTS_DIR):
        if file not in file_set:
            os.remove(os.path.join(PGET_KNOWN_WEIGHTS_DIR, file))

    p = find_pget_exe()
    # pget each of the files into the new directory
    for file in file_set:
        # If we have an upstream, make the URL <upstream>/<file> but strip http(s)://
        # from the <file> URL
        if upstream:
            if file.startswith('http'):
                file = re.sub(r'https?://', '', file)
            file = f'{upstream}/{file}'
        try:
            # Download to tmp directory, then move into PGET_KNOWN_WEIGHTS_DIR directory
            subprocess.run(
                [p, file, os.path.join(PGET_KNOWN_WEIGHTS_DIR, 'tmp', h.hexdigest())],
                check=True,
            )
            shutil.move(
                os.path.join(PGET_KNOWN_WEIGHTS_DIR, 'tmp', h.hexdigest()),
                os.path.join(PGET_KNOWN_WEIGHTS_DIR, h.hexdigest()),
            )
        except Exception as e:
            print(f'Error downloading {file}: {e}')
            # Continue on anyways to get the rest of the files


if __name__ == '__main__':
    args = parser.parse_args()
    main(
        args.query_url, args.query_id, args.upstream_url, args.auth_token, args.max_size
    )
