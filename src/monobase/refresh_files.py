#!/usr/bin/env python3

import argparse
import hashlib
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import time
import urllib
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus

from monobase.util import setup_logging

MONOBASE_PREFIX = os.environ.get('MONOBASE_PREFIX', '/srv/r8/monobase')
PGET_BIN = os.environ.get('PGET_BIN', os.path.join(MONOBASE_PREFIX, 'bin/pget-bin'))

parser = argparse.ArgumentParser('refresh_files')
parser.add_argument('--weights-dir', type=str, required=True)
parser.add_argument('--max-size', type=int, default=1024 * 1024 * 1024 * 1024)  # 1TiB
parser.add_argument('--sleep-interval', type=int, default=60 * 60 * 24)  # 24 hours

log = logging.getLogger(__name__)


def find_pget_exe() -> str:
    # PGET_BIN is executable
    if os.path.isfile(PGET_BIN) and os.access(PGET_BIN, os.X_OK):
        return PGET_BIN
    # Look for real executable in PATH
    for p in os.environ['PATH'].split(os.pathsep):
        f = shutil.which('pget', path=p)
        if f is not None and f != __file__:
            return f
    log.error('Cannot find pget executable')
    sys.exit(1)


def sync(args: argparse.Namespace, endpoint: str) -> None:
    resp = urllib.request.urlopen(endpoint)
    assert resp.status == HTTPStatus.OK, 'failed to get query result'

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
    assert len(results) >= 0, 'empty query results'

    files: dict[str, str] = {}
    total_size = 0

    # Parse results to figure out what files to download
    for result in results:
        data = result.get('data', {})
        if 'cache.request.resolved_url' not in data:
            log.error('Missing object URL in query result: %s', result)
            continue

        # Check we won't violate the total size by downloading this file
        if 'cache.response.object_size' not in data:
            log.error('Missing object size in query result: %s', result)
            continue
        size = data['cache.response.object_size']
        if (total_size + size) > args.max_size:
            log.info('Max size reached: %d files, %d bytes', len(files), total_size)
            break
        total_size += size

        url = data['cache.request.resolved_url']
        h = hashlib.sha256(url.encode()).hexdigest()
        files[h] = url
        log.info('%s %12d %s', h, size, url)

    os.makedirs(args.weights_dir, exist_ok=True)

    # Delete files that should no longer be here so we keep the directory clean
    for file in os.listdir(args.weights_dir):
        if file not in files:
            log.info('Deleting stale file: %s', file)
            os.remove(os.path.join(args.weights_dir, file))

    p = find_pget_exe()
    # pget each of the files into the new directory
    for h, url in files.items():
        try:
            # Download to tmp directory, then move into PGET_KNOWN_WEIGHTS_DIR directory
            subprocess.run(
                [p, url, os.path.join(args.weights_dir, f'tmp-{h}')],
                check=True,
            )
            shutil.move(
                os.path.join(args.weights_dir, f'tmp-{h}'),
                os.path.join(args.weights_dir, h),
            )
        except Exception as e:
            log.error(f'Error downloading {url}: {e}')
            # Continue on anyways to get the rest of the files


def main(args: argparse.Namespace) -> None:
    host = os.environ.get('PGET_CACHE_SERVICE_HOSTNAME')
    assert host is not None, 'PGET_CACHE_SERVICE_HOSTNAME not set'
    endpoint = f'{host}/topk'
    while True:
        try:
            sync(args, endpoint)
            log.info('Sleeping for %d seconds', args.sleep_interval)
            time.sleep(args.sleep_interval)
        except Exception as e:
            log.error('Sync failed: %s', e)
            # Possibly rate limited, back off for a random period as jitter
            bo = random.randint(60, 600)
            log.info('Sleeping for %d seconds', bo)
            time.sleep(bo)


if __name__ == '__main__':
    setup_logging()
    main(parser.parse_args())
