from collections import namedtuple


MonoGen = namedtuple('MonoGen', ['id', 'cuda', 'cudnn', 'python', 'torch', 'pip_pkgs'])

TEST_MONOGENS: list[MonoGen] = [
    MonoGen(
        id=0,
        cuda={'12.4': '12.4.1_550.54.15'},
        cudnn={'9': '9.1.0.70'},
        python={'3.12': '3.12.6'},
        torch=['2.4.1'],
        pip_pkgs=['cog==0.9.23', 'opencv-python==4.10.0.84']
    ),
]

PROD_MONOGENS: list[MonoGen] = [
    MonoGen(
        id=0,
        cuda={
            '12.4': '12.4.1_550.54.15',
            '12.1': '12.1.1_530.30.02',
            '11.8': '11.8.0_520.61.05',
        },
        cudnn={
            '9': '9.1.0.70',
            '8': '8.9.7.29',
        },
        python={
            '3.8': '3.8.20',
            '3.9': '3.9.20',
            '3.10': '3.10.15',
            '3.11': '3.11.10',
            '3.12': '3.12.6',
        },
        torch=[
            '2.0.0', '2.0.1',
            '2.1.0', '2.1.1', '2.1.2',
            '2.2.0', '2.2.1', '2.2.2',
            '2.3.0', '2.3.1',
            '2.4.0', '2.4.1',
        ],
        pip_pkgs=[
            'https://github.com/replicate/cog/archive/refs/heads/add-waiting-env.zip',
            'opencv-python==4.10.0.84',
        ],
    ),
]

MONOGENS: dict[str, list[MonoGen]] = {
    'test': TEST_MONOGENS,
    'prod': PROD_MONOGENS,
}


def validate():
    for env, gens in MONOGENS.items():
        for i, g in enumerate(gens):
            assert g.id == i, f'[{env}] MonoGen.id {g.id} does not equal index {i}'
            for k, v in g.cuda.items():
                assert v.startswith(f'{k}.'), f'[{env}] CUDA {v} is not {k}'
            for k, v in g.cudnn.items():
                assert v.startswith(f'{k}.'), f'[{env}] CuDNN {v} is not {k}'
            for k, v in g.python.items():
                assert v.startswith(f'{k}.'), f'[{env}] Python {v} is not {k}'
            for p in g.pip_pkgs:
                assert '==' in p or p.startswith('https://'), f'PIP package {p} is not pinned'


validate()
