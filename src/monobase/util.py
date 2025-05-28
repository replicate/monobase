import argparse
import contextlib
import datetime
import glob
import hashlib
import json
import logging
import os
import os.path
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

import structlog
from structlog.typing import EventDict

HERE = os.path.dirname(os.path.abspath(__file__))
IN_KUBERNETES = os.environ.get('KUBERNETES_SERVICE_HOST') is not None
NODE_FEATURE_LABEL_FILE = '/etc/kubernetes/node-feature-discovery/features.d/monobase'
DONE_FILE_BASENAME = '.done'
MINIMUM_VALID_JSON_SIZE = len('{"version":"dev"}')
VERSION_REGEX = re.compile(
    r'^(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+)(\.(?P<extra>.+))?)?)?'
)

log = logging.getLogger(__name__)

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
    def parse(cls, s: str | None) -> 'Version':
        if s is None:
            return cls(0, 0, 0, '', '')
        m = VERSION_REGEX.search(s)
        if m is None:
            raise ValueError(f'Invalid version string: {s}')
        major = int(m.group('major'))
        minor = int(m.group('minor') or 0)
        patch = int(m.group('patch') or 0)
        extra = m.group('extra') or ''
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


def _get_tree_sha1sum(d: str) -> str:
    with contextlib.chdir(d):
        entries = glob.glob('./**', recursive=True, include_hidden=True)
        entries = [
            entry for entry in entries if not entry.endswith('/' + DONE_FILE_BASENAME)
        ]
        entries.sort()

        tree_sha1sum = hashlib.sha1(usedforsecurity=False)
        for entry in entries:
            tree_sha1sum.update(entry.encode())

        return tree_sha1sum.hexdigest()


def _is_done(d: str) -> bool:
    try:
        with open(os.path.join(d, DONE_FILE_BASENAME)) as done_file:
            done_state = json.load(done_file)
            return _get_tree_sha1sum(d) == done_state.get('sha1sum', '')
    except Exception:
        return False


def require_done_or_rm(d: str) -> bool:
    """
    This function checks for the presence of a 'done file', and, if one is not found, or
    if the directory tree "shape" sha1sum does not match, removes the tree at `d` so that
    the code requiring the done file can re-run.
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
                'sha1sum': _get_tree_sha1sum(d),
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
            parts = line.split('==', 1)
        elif '@' in line:
            parts = line.split('@', 1)
        elif os.path.exists(line):
            # Local file, version unknown, use exact path as version
            p = os.path.abspath(line)
            parts = [p, p]
        else:
            raise ValueError(f'invalid requirement: {line}')
        vs = parts[1].strip()
        try:
            versions[parts[0].strip()] = Version.parse(vs)
        except ValueError:
            versions[parts[0].strip()] = vs
    return versions


def du(d: str) -> None:
    subprocess.run(['du', '-ch', '-d', '1', d], check=True)


def replace_level_with_severity(
    _: logging.Logger, __: str, event_dict: EventDict
) -> EventDict:
    """
    Replace the level field with a severity field as understood by Stackdriver
    logs.
    """
    if 'level' in event_dict:
        event_dict['severity'] = event_dict.pop('level').upper()
    return event_dict


def setup_logging() -> None:
    # Switch to human-friendly log output if LOG_FORMAT environment variable is
    # set to "development".
    development_logs = os.environ.get('LOG_FORMAT', '') == 'development'

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt='iso'),
    ]

    if development_logs:
        # In development, set `exc_info` on the log event if the log method is
        # `exception` and `exc_info` is not already set.
        #
        # Rendering of `exc_info` is handled by ConsoleRenderer.
        processors.append(structlog.dev.set_exc_info)
    else:
        # Outside of development mode `exc_info` must be set explicitly when
        # needed, and is translated into a formatted `exception` field.
        processors.append(structlog.processors.format_exc_info)
        # Set `severity`, not `level`, for compatibility with Google
        # Stackdriver logging expectations.
        processors.append(replace_level_with_severity)

    # Stackdriver logging expects a "message" field, not "event"
    processors.append(structlog.processors.EventRenamer('message'))

    structlog.configure(
        processors=processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    if development_logs:
        log_renderer = structlog.dev.ConsoleRenderer(event_key='message')  # type: ignore
    else:
        log_renderer = structlog.processors.JSONRenderer()  # type: ignore

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
