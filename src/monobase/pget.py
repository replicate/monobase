#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Dict

MONOBASE_PREFIX = os.environ.get('MONOBASE_PREFIX', '/srv/r8/monobase')
PGET_BIN = os.environ.get('PGET_BIN', os.path.join(MONOBASE_PREFIX, 'bin/pget-bin'))
PGET_METRICS_ENDPOINT = os.environ.get('PGET_METRICS_ENDPOINT')
FUSE_MOUNT = os.environ.get('FUSE_MOUNT', '/srv/r8/fuse-rpc')
PROC_FILE = os.path.join(FUSE_MOUNT, 'proc', 'pget')
PGET_CACHED_PREFIXES = os.environ.get('PGET_CACHE_URI_PREFIX', '')

HF_HOSTS = {
    'cdn-lfs-us-1.hf.co',
    'cdn-lfs-eu-1.hf.co',
    'cdn-lfs.hf.co',
    'cas-bridge.xethub.hf.co',
}

parser = argparse.ArgumentParser('pget')

# All arguments are ignored, they are here to make argument parsing compatible with pget
parser.add_argument('-m', '--chunk-size', type=str, metavar='string', default='125M')
parser.add_argument('-c', '--concurrency', type=int, metavar='int', default='128')
parser.add_argument('--connection-timeout', type=str, metavar='duration', default='5s')
parser.add_argument('-x', '--extract', default=False, action='store_true')
parser.add_argument('-f', '--force', default=False, action='store_true')
parser.add_argument('--log-level', type=str, metavar='string', default='info')
parser.add_argument(
    '--pid-file', type=str, metavar='string', default='/run/user/1000/pget.pid'
)
parser.add_argument('--resolve', type=str, metavar='strings', default=None)
parser.add_argument('-r', '--retries', type=int, metavar='int', default=5)
parser.add_argument('-v', '--verbose', default=False, action='store_true')


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


# https://github.com/replicate/pget/blob/main/cmd/multifile/manifest.go
def parse_manifest(manifest: str) -> Dict[str, str]:
    f = sys.stdin if manifest == '-' else open(manifest, 'r')
    d = {}
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        url, dest = line.split()
        assert dest not in d
        d[dest] = url
    return d


def is_hf_presigned(u: urllib.parse.ParseResult) -> bool:
    # These are likely HuggingFace CloudFront URLs, redirected from
    # https://huggingface.co/<org>/<repo>/resolve/<sha256>/<filename>
    # Strip query params to reduce noise
    # https://discuss.huggingface.co/t/how-to-get-a-list-of-all-huggingface-download-redirections-to-whitelist/30486/11
    return u.hostname in HF_HOSTS


def is_s3_presigned(u: urllib.parse.ParseResult) -> bool:
    return (
        u.hostname is not None
        and '.s3.' in u.hostname
        and u.hostname.endswith('.amazonaws.com')
    )


def normalize_url(url: str) -> str:
    u = urllib.parse.urlparse(url)
    if is_hf_presigned(u) or is_s3_presigned(u):
        # Reuse <schema>://<host>:<port>/<path> from original URL
        # Strip query params
        return urllib.parse.urljoin(url, u.path)
    return url


def send_pget_metrics(url: str, size: int) -> None:
    if PGET_METRICS_ENDPOINT is None:
        return
    payload = {
        'source': 'pget-fuse',
        'type': 'download',
        'data': {
            'url': url,
            'size': size,
        },
    }
    data = json.dumps(payload).encode('utf-8')
    try:
        urllib.request.urlopen(PGET_METRICS_ENDPOINT, data=data, timeout=1).read()
    except Exception:
        # Ignore errors
        pass


def multi_pget(manifest: str, force: bool) -> None:
    urls = parse_manifest(manifest)
    for dest, url in urls.items():
        single_pget(url, dest, extract=False, force=force)


def single_pget(url: str, dest: str, extract: bool, force: bool) -> None:
    if not force:
        assert not os.path.exists(dest)

    for prefix in PGET_CACHED_PREFIXES.split(' '):
        # If the URL has a prefix that matches one of the
        # cached prefixes, fall back to pget directly
        assert not url.startswith(prefix)

    req = urllib.request.Request(url, method='HEAD')
    resp = urllib.request.urlopen(req)

    assert resp.status == 200
    length = int(resp.getheader('Content-Length'))
    etag = resp.getheader('Etag')
    modified = resp.getheader('Last-Modified')
    # Normalize URL to avoid thrashing cache
    fingerprint = f'{normalize_url(url)}|{length}|{etag}|{modified}'
    sha = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
    name = f'pget/sha256/{sha}'
    payload = {'name': name, 'size': length, 'url': url}

    print(f'pget {url} {dest}', file=sys.stderr)
    with open(PROC_FILE, 'w') as f:
        json.dump(payload, f)

    # Send metrics if endpoint is set
    # Send after writing proc file, i.e. no FUSE error
    send_pget_metrics(url, length)

    src = os.path.join(FUSE_MOUNT, name)
    if extract:
        # dest is a directory
        os.makedirs(dest, exist_ok=True)
        # pget does not support zip
        # tar will overwrite existing files
        cmd = ['tar', '-xf', src, '-C', dest]
        subprocess.run(cmd, check=True)
    else:
        d = os.path.dirname(dest)
        if d != '':
            os.makedirs(d, exist_ok=True)
        if force and os.path.exists(dest):
            os.unlink(dest)
        os.symlink(src, dest)


def smart_pget() -> None:
    # Fall back if no FUSE
    assert os.path.exists(PROC_FILE)

    args, vargs = parser.parse_known_args()

    # FUSE server is not configured to use storage cache
    # So these tar files are downloaded from CDN at lower speed
    # That plus tar files are not lazily loadable defeats the point of having them in FUSE cache
    assert not args.extract

    # Supported:
    # pget [flags] <URL> <dest>
    # pget [flags] multifile <file>
    assert len(vargs) == 2
    if vargs[0] == 'multifile':
        # multifile does not support extract
        assert not args.extract
        multi_pget(vargs[1], args.force)
    else:
        url, dst = vargs
        u = urllib.parse.urlparse(url)

        # Prevent `pget <URL> <dst.tar>` without --extract
        assert not u.path.endswith('.tar')

        single_pget(url, dst, args.extract, args.force)


if __name__ == '__main__':
    try:
        smart_pget()
    except Exception:
        p = find_pget_exe()
        os.execv(p, [p] + sys.argv[1:])
