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
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import Optional

from monobase.util import setup_logging

MONOBASE_PREFIX = os.environ.get('MONOBASE_PREFIX', '/srv/r8/monobase')
METADATA_FILE = 'metadata.json'
PGET_BIN = os.environ.get('PGET_BIN', os.path.join(MONOBASE_PREFIX, 'bin/pget-bin'))

parser = argparse.ArgumentParser('refresh_files')
parser.add_argument('--weights-dir', type=str, required=True)
parser.add_argument('--max-size', type=int, default=1024 * 1024 * 1024 * 1024)  # 1TiB
parser.add_argument('--sleep-interval', type=int, default=60 * 60 * 24)  # 24 hours

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Object:
    url: str
    size: int
    etag: str


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


def get_object(url: str) -> Optional[Object]:
    req = urllib.request.Request(url, method='HEAD')
    resp = urllib.request.urlopen(req)
    if resp.status != HTTPStatus.OK:
        return None
    etag = resp.getheader('Etag')
    size = int(resp.getheader('Content-Length'))
    return Object(url, size, etag)


def read_metadata(weights_dir: str) -> dict[str, Object]:
    r: dict[str, Object] = {}
    p = os.path.join(weights_dir, METADATA_FILE)
    if not os.path.exists(p):
        return r
    with open(p, 'r') as f:
        j = json.load(f)
        for k, v in j.items():
            r[k] = Object(**v)
        return r


def write_metadata(weights_dir: str, metadata: dict[str, Object]) -> None:
    j = {}
    for k, v in metadata.items():
        j[k] = v.__dict__
    p = os.path.join(weights_dir, METADATA_FILE)
    with open(p, 'w') as f:
        json.dump(j, f, indent=2)


def sync(args: argparse.Namespace, endpoint: str) -> None:
    start = datetime.now()

    resp = urllib.request.urlopen(endpoint)
    assert resp.status == HTTPStatus.OK, 'failed to get query result'

    if args.honeycomb_api_key:
        subprocess.run(
            [
                'honeymarker',
                '-k',
                args.honeycomb_api_key,
                'add',
                '-d',
                args.dataset,
                '-e',
                str(int(start.timestamp())),
                '-m',
                'Start on-node cached files sync script',
            ]
        )

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

    new_meta: dict[str, Object] = {}
    deleted = 0
    downloaded = 0
    total_size = 0

    # Parse results to figure out what files to download
    for result in results:
        data = result.get('data', {})
        if 'cache.request.resolved_url' not in data:
            log.error('Missing object URL in query result: %s', result)
            continue

        url = data['cache.request.resolved_url']
        obj = get_object(url)
        if obj is None:
            continue

        # Check we won't violate the total size by downloading this file
        if (total_size + obj.size) > args.max_size:
            log.info('Max size reached: %d files, %d bytes', len(new_meta), total_size)
            break
        total_size += obj.size

        h = hashlib.sha256(url.encode()).hexdigest()
        new_meta[h] = obj

    os.makedirs(args.weights_dir, exist_ok=True)

    # Delete files that should no longer be here so we keep the directory clean
    old_meta = read_metadata(args.weights_dir)
    for file in os.listdir(args.weights_dir):
        if file == METADATA_FILE:
            continue

        # URL, size, etag must all match for a file to be kept
        old_obj = old_meta.get(file)
        new_obj = new_meta.get(file)
        if new_obj is None or old_obj != new_obj:
            log.info('Deleting stale file: %s', file)
            p = os.path.join(args.weights_dir, file)
            deleted += os.stat(p).st_size
            os.remove(p)

    p = find_pget_exe()
    # pget each of the files into the new directory
    for h, obj in new_meta.items():
        tmp = os.path.join(args.weights_dir, f'tmp-{h}')
        dst = os.path.join(args.weights_dir, h)
        if os.path.exists(dst):
            continue
        try:
            # Download to tmp directory, then move into PGET_KNOWN_WEIGHTS_DIR directory
            subprocess.run([p, obj.url, tmp], check=True)
            shutil.move(tmp, dst)
            downloaded += os.stat(dst).st_size
        except Exception as e:
            log.error('Error downloading %s: %s', obj.url, e)
            # Continue on anyways to get the rest of the files

    write_metadata(args.weights_dir, new_meta)

    end = datetime.now()
    log.info(
        'Sync completed in %f seconds, deleted %f MiB, downloaded %f MiB',
        (end - start).total_seconds(),
        deleted / 1024.0 / 1024.0,
        downloaded / 1024.0 / 1024.0,
    )

    if args.honeycomb_api_key:
        subprocess.run(
            [
                'honeymarker',
                '-k',
                args.honeycomb_api_key,
                'add',
                '-d',
                args.dataset,
                '-e',
                str(int(end.timestamp())),
                '-m',
                'Start on-node cached files sync script',
            ]
        )


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
            bo = random.randint(1, 60)
            log.info('Sleeping for %d seconds', bo)
            time.sleep(bo)


if __name__ == '__main__':
    setup_logging()
    main(parser.parse_args())
