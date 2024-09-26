from collections import namedtuple
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


class Version(namedtuple('Version', ['major', 'minor', 'patch', 'repr'])):
    p = re.compile(r'^(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+))?)?')

    @classmethod
    def parse(cls, s):
        m = Version.p.search(s)
        major = int(m.group('major'))
        minor = int(m.group('minor') or 0)
        patch = int(m.group('patch') or 0)
        return cls(major, minor, patch, s)

    def __repr__(self):
        return self.repr


def is_done(d: str) -> bool:
    if os.path.exists(os.path.join(d, '.done')):
        return True
    else:
        shutil.rmtree(d, ignore_errors=True)
        return False


def mark_done(d: str) -> None:
    with open(os.path.join(d, '.done'), 'w') as f:
        f.write('')
