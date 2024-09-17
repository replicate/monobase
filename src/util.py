#!/usr/bin/env python3

from collections import namedtuple
import re
import subprocess


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


def run(cmd, args):
    if args.verbose:
        print(' '.join(cmd))
    subprocess.run(cmd, check=True)
