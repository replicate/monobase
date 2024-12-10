import argparse
import os.path

from monobase.util import Version, parse_requirements

parser = argparse.ArgumentParser(description='Diff monobase requirements')
parser.add_argument('id', nargs=2, type=int, help='Generation ID')


def diff_versions(
    venv: str, vs0: dict[str, str | Version], vs1: dict[str, str | Version]
) -> None:
    for k in sorted(list(vs0.keys()) + list(vs1.keys())):
        if k in vs0 and k not in vs1:
            print(f'{venv}\t{k}\t{vs0[k]}\t-')
        elif k not in vs0 and k in vs1:
            print(f'{venv}\t{k}\t-\t{vs1[k]}')
        elif vs0[k] != vs1[k]:
            print(f'{venv}\t{k}\t{vs0[k]}\t{vs1[k]}')


def diff(id0: int, id1: int) -> None:
    rdir = os.path.join(os.path.dirname(__file__), 'requirements')
    g0, g1 = f'g{id0:05d}', f'g{id1:05d}'
    rdir0 = os.path.join(rdir, g0)
    rdir1 = os.path.join(rdir, g1)

    venvs0 = os.listdir(rdir0)
    venvs1 = os.listdir(rdir1)

    venvs = sorted(set(venvs0) - set(venvs1))
    if len(venvs) > 0:
        for v in venvs:
            v = v.rstrip('.txt')
            print(f'- {v}')

    venvs = sorted(set(venvs1) - set(venvs0))
    if len(venvs) > 0:
        for v in venvs:
            v = v.rstrip('.txt')
            print(f'+ {v}')

    for venv in sorted(set(venvs0).intersection(set(venvs1))):
        with open(os.path.join(rdir0, venv), 'r') as f:
            vs0 = parse_requirements(f.read())
        with open(os.path.join(rdir1, venv), 'r') as f:
            vs1 = parse_requirements(f.read())
        diff_versions(venv.rstrip('.txt'), vs0, vs1)


if __name__ == '__main__':
    args = parser.parse_args()
    diff(args.id[0], args.id[1])
