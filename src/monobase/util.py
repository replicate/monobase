import argparse
import datetime
import json
import logging
import os.path
import re
import shutil
import sys
from dataclasses import dataclass
from typing import Iterable

DONE_FILE_BASENAME = '.done'
MINIMUM_VALID_JSON_SIZE = len('{"version":"dev"}')
VERSION_REGEX = re.compile(
    r'^(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+)(\.(?P<extra>.+))?)?)?'
)

try:
    from monobase._version import __version__
except ImportError:
    __version__ = 'dev'


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int
    extra: str
    repr: str

    @classmethod
    def parse(cls, s: str) -> 'Version':
        m = VERSION_REGEX.search(s)
        if m is None:
            raise ValueError(f'Invalid version string: {s}')
        major = int(m.group('major'))
        minor = int(m.group('minor') or 0)
        patch = int(m.group('patch') or 0)
        extra = m.group('extra')
        return cls(major, minor, patch, extra, s)

    def __repr__(self) -> str:
        return self.repr


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--environment',
        metavar='ENV',
        default='prod',
        choices=['test', 'prod'],
        help='environment [test, prod], default=prod',
    )
    parser.add_argument(
        '--min-gen-id',
        metavar='N',
        type=int,
        default=0,
        help='minimum generation ID, default=0',
    )
    parser.add_argument(
        '--max-gen-id',
        metavar='N',
        type=int,
        default=sys.maxsize,
        help='maximum generation ID, default=inf',
    )


def _is_done(d: str) -> bool:
    full_path = os.path.join(d, DONE_FILE_BASENAME)
    return (
        os.path.exists(full_path)
        and os.stat(full_path).st_size > MINIMUM_VALID_JSON_SIZE
    )


def require_done_or_rm(d: str) -> bool:
    """
    This function checks for the presence of a 'done file', and, if one is not found,
    removes the tree at `d` so that the code requiring the done file can re-run.
    """
    if _is_done(d):
        return True

    if os.path.exists(d):
        shutil.rmtree(d)

    return False


def mark_done(d: str, *, kind: str, **attributes) -> None:
    with open(os.path.join(d, DONE_FILE_BASENAME), 'w') as f:
        json.dump(
            {
                'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
                'attributes': {
                    'monobase_version': __version__,
                    'monobase_kind': kind,
                }
                | {
                    f'monobase_{kind}.{key}': value for key, value in attributes.items()
                },
            },
            f,
            sort_keys=True,
            indent=2,
        )
        f.write('\n')


def desc_version(it: Iterable[str]) -> list[str]:
    return sorted(it, key=Version.parse, reverse=True)


def desc_version_key(d: dict[str, str]) -> list[tuple[str, str]]:
    return sorted(d.items(), key=lambda kv: Version.parse(kv[0]), reverse=True)


def parse_requirements(req: str) -> dict[str, str | Version]:
    versions: dict[str, str | Version] = {}
    for line in req.splitlines():
        line = line.strip()
        if line == '' or line.startswith('#') or line.startswith('--'):
            continue
        if '==' in line:
            parts = line.split('==')
        elif '@' in line:
            parts = line.split('@')
        else:
            raise ValueError(f'invalid requirement: {line}')
        assert len(parts) == 2, f'invalid requirement: {line}'
        vs = parts[1].strip()
        try:
            versions[parts[0].strip()] = Version.parse(vs)
        except ValueError:
            versions[parts[0].strip()] = vs
    return versions


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s\t%(levelname)s\t%(filename)s:%(lineno)d\t%(message)s'
        )
    )
    logger.addHandler(handler)
