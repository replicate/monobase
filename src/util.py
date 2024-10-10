from dataclasses import dataclass
import argparse
import logging
import os.path
import re
import shutil
import sys


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s\t%(levelname)s\t%(filename)s:%(lineno)d\t%(message)s'))
logger.addHandler(handler)

VERSION_REGEX = re.compile(
        r'^(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+)(\.(?P<extra>.+))?)?)?')


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int
    extra: str
    repr: str

    @classmethod
    def parse(cls, s):
        m = VERSION_REGEX.search(s)
        major = int(m.group('major'))
        minor = int(m.group('minor') or 0)
        patch = int(m.group('patch') or 0)
        extra = m.group('extra')
        return cls(major, minor, patch, extra, s)

    def __repr__(self):
        return self.repr


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--environment', metavar='ENV', default='prod', choices=['test', 'prod'],
                        help='environment [test, prod], default=prod')
    parser.add_argument('--min-gen-id', metavar='N', type=int, default=0,
                        help='minimum generation ID, default=0')
    parser.add_argument('--max-gen-id', metavar='N', type=int, default=sys.maxsize,
                        help='maximum generation ID, default=inf')


def is_done(d: str) -> bool:
    if os.path.exists(os.path.join(d, '.done')):
        return True
    else:
        shutil.rmtree(d, ignore_errors=True)
        return False


def mark_done(d: str) -> None:
    with open(os.path.join(d, '.done'), 'w') as f:
        f.write('')
