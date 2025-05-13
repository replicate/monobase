import argparse
import itertools
import json
import logging
import os.path
import pathlib
from tempfile import TemporaryDirectory

from monobase.monogen import MONOGENS, MonoGen
from monobase.torch import get_torch_spec
from monobase.util import (
    Version,
    add_arguments,
    desc_version,
    desc_version_key,
    setup_logging,
)
from monobase.uv import update_venv

parser = argparse.ArgumentParser(description='Update monobase requirements')
add_arguments(parser)

log = logging.getLogger(__name__)


def update_generation(
    args: argparse.Namespace, tmp: TemporaryDirectory, mg: MonoGen, latest: bool
) -> None:
    log.info(f'Updating monobase generation {mg.id}')
    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    gid = f'g{mg.id:05d}'
    rdir = os.path.join(os.path.dirname(__file__), f'requirements{suffix}', gid)
    os.makedirs(rdir, exist_ok=True)

    # Always include CPU Torch
    cudas = ['cpu'] + desc_version(mg.cuda.keys())
    venvs = []
    for (p, pf), t, c in itertools.product(
        desc_version_key(mg.python),
        desc_version(mg.torch),
        cudas,
    ):
        updated = update_venv(rdir, tmp.name, p, pf, t, c, mg.pip_pkgs)
        if updated:
            venvs.append({'python': p, 'torch': t, 'cuda': c})

    if latest:
        torch_cudas: dict[str, list[str]] = {}
        for tv in mg.torch:
            spec = get_torch_spec(Version.parse(tv))
            if spec is None:
                continue
            torch_cudas[tv] = [c for c in spec.cudas if c != 'cpu']
        # Write a version matrix for cog build, etc.
        matrix = {
            'id': mg.id,
            'cuda_versions': list(mg.cuda.keys()),
            'cudnn_versions': list(mg.cudnn.keys()),
            'python_versions': list(mg.python.keys()),
            'torch_versions': mg.torch,
            'torch_cudas': torch_cudas,
            'venvs': venvs,
        }
        project_dir = pathlib.Path(__file__).absolute().parent.parent.parent
        with open(os.path.join(project_dir, 'matrix.json'), 'w') as f:
            json.dump(matrix, f, indent=2)
        dest = os.path.join(
            os.path.dirname(__file__), f'requirements{suffix}', 'latest'
        )
        if os.path.exists(dest):
            os.remove(dest)
        os.symlink(gid, dest)

        # Write all Python versions for test scripts
        with open(os.path.join(project_dir, 'python-versions'), 'w') as f:
            for v in mg.python.keys():
                print(v, file=f)


def update(args: argparse.Namespace) -> None:
    tmp = TemporaryDirectory(prefix='monobase-')
    gens = []
    for i, mg in enumerate(sorted(MONOGENS[args.environment], reverse=True)):
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        latest = args.environment == 'prod' and i == 0
        update_generation(args, tmp, mg, latest)
        gens.append(mg.id)

    log.info(f'Monobase update completed: {sorted(gens)}')


if __name__ == '__main__':
    setup_logging()
    update(parser.parse_args())
