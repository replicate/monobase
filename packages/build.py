#!/usr/bin/env python3

import argparse
import os
import subprocess

parser = argparse.ArgumentParser(description='Run a script in a monobase environment')
parser.add_argument(
    '--from-tag',
    metavar='TAG',
    default='r8.im/monobase:latest',
    help='Monobase image tag to build from',
)
parser.add_argument(
    '--python',
    metavar='VERSION',
    required=True,
    help='Python version to install in monobase, must be <major.minor>',
)
parser.add_argument(
    '--cuda',
    metavar='VERSION',
    default=None,
    help='CUDA version to install in monobase, must be <major.minor>',
)
parser.add_argument(
    '--torch',
    metavar='VERSION',
    required=True,
    help='Torch version to install in monobase, must be <major.minor.patch>',
)
parser.add_argument(
    '--dst',
    metavar='DIR',
    default='/tmp',
    help='Directory to mount read-write as /dst inside the container',
)
parser.add_argument(
    'script',
    metavar='SCRIPT',
    nargs='?',
    help='Script to run in monobase',
)


def generate_dockerfile(args: argparse.Namespace, env: dict[str, str]) -> str:
    # No user layer since it's not needed for building Python packages
    build_cmd = ' '.join(
        [
            'RUN',
            '--mount=type=cache,target=/srv/r8/monobase/uv/cache,id=uv-cache',
            '--mount=type=cache,target=/var/cache/monobase/,id=var-cache',
            '/opt/r8/monobase/run.sh monobase.build --mini',
        ]
    )
    dockerfile = (
        [
            f'FROM {args.from_tag}',
            # UV cache is a cache mount and doesn't support hard links
            'ENV UV_LINK_MODE=copy',
        ]
        + [f'ENV {k}={v}' for k, v in env.items()]
        + [
            build_cmd,
            # Create an empty user venv
            f'RUN uv venv --python {env["R8_PYTHON_VERSION"]} /root/.venv',
            'ENV VIRTUAL_ENV=/root/.venv',
            # Python version for uv build, etc.
            f'ENV UV_PYTHON={env["R8_PYTHON_VERSION"]}',
            'RUN mkdir /build /src /dst',
            'WORKDIR /build',
            'ENTRYPOINT ["/bin/bash", "--rcfile", "/opt/r8/monobase/activate.sh"]',
        ]
    )
    return '\n'.join(dockerfile)


def run(args: argparse.Namespace) -> None:
    env = {
        'R8_COG_VERSION': 'coglet',
        'R8_PYTHON_VERSION': args.python,
    }
    tag = f'monobase:python{args.python}'
    if args.torch is not None:
        env['R8_TORCH_VERSION'] = args.torch
        tag = f'{tag}-torch{args.torch}'
    if args.cuda is not None:
        env['R8_CUDA_VERSION'] = args.cuda
        env['R8_CUDNN_VERSION'] = '9'
        tag = f'{tag}-cuda{args.cuda}'

    print(f'Building monobase {tag}')
    print()

    dockerfile = generate_dockerfile(args, env)
    print('Dockerfile:')
    print(dockerfile)

    build_cmd = ['docker', 'build', '--tag', tag, '--file', '-', '.']
    subprocess.run(build_cmd, check=True, input=dockerfile.encode('utf-8'))

    run_cmd = [
        'docker',
        'run',
        '--rm',
        '-it',
        '--volume',
        f'{os.path.abspath(args.dst)}:/dst:rw',
        tag,
    ]
    if args.script:
        with open(args.script, 'r') as f:
            script = f.read()
        run_cmd = run_cmd + ['-c', script]
    os.execvp('docker', run_cmd)


if __name__ == '__main__':
    run(parser.parse_args())
