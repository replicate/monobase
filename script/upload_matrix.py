#!/usr/bin/env python3

import json
import pathlib
import subprocess
import tempfile
import urllib.request

UPLOAD_URI = 's3://replicate-monobase-packages/matrix.json'


def latest_coglet():
    url = 'https://api.github.com/repos/replicate/cog-runtime/releases/latest'
    content = urllib.request.urlopen(url).read()
    blob = json.loads(content)
    version = blob['name']
    url = blob['assets'][0]['browser_download_url']
    print(f'coglet {version} @ {url}')
    return {'version': version, 'url': url}


def latest_hf_transfer():
    url = 'https://api.github.com/repos/replicate/hf_transfer/releases/latest'
    content = urllib.request.urlopen(url).read()
    blob = json.loads(content)
    version = blob['name']
    for a in blob['assets']:
        # We build 2 wheels, abi3 for Python 3.8+ and cp313t for free threaded Python
        if a['name'].endswith('.whl') and '-abi3-' in a['name']:
            url = a['browser_download_url']
            print(f'hf_transfer {version} @ {url}')
            return {'version': version, 'url': url}
    raise Exception('could not find hf_transfer wheel')


if __name__ == '__main__':
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    matrix = json.load((base_dir / 'matrix.json').open())
    matrix['latest_coglet'] = latest_coglet()
    matrix['latest_hf_transfer'] = latest_hf_transfer()
    _, p = tempfile.mkstemp(suffix='.json', prefix='matrix-')
    with open(p, 'w') as f:
        json.dump(matrix, indent=2, fp=f)

    subprocess.run(['aws', 's3', 'cp', p, UPLOAD_URI], check=True)
