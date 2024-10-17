from tempfile import TemporaryDirectory
import argparse
import logging
import os.path

from monogen import MONOGENS, MonoGen
from util import add_arguments, desc_version, desc_version_key, setup_logging
from uv import update_venv

parser = argparse.ArgumentParser(description='Update monobase requirements')
add_arguments(parser)


def update_generation(
    args: argparse.Namespace, tmp: TemporaryDirectory, mg: MonoGen
) -> None:
    logging.info(f'Updating monobase generation {mg.id}')
    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    rdir = os.path.join(
        os.path.dirname(__file__), f'requirements{suffix}', f'g{mg.id:05d}'
    )
    os.makedirs(rdir, exist_ok=True)

    for p, pf in desc_version_key(mg.python):
        for t in desc_version(mg.torch):
            for c in desc_version(mg.cuda.keys()):
                update_venv(rdir, tmp.name, p, pf, t, c, mg.pip_pkgs)


def update(args: argparse.Namespace) -> None:
    tmp = TemporaryDirectory(prefix='monobase-')
    gens = []
    for mg in sorted(MONOGENS[args.environment], reverse=True):
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        update_generation(args, tmp, mg)
        gens.append(mg.id)

    logging.info(f'Monobase update completed: {sorted(gens)}')


if __name__ == '__main__':
    setup_logging()
    update(parser.parse_args())
