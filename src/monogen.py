from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class MonoGen:
    id: int
    cuda: dict[str, str]
    cudnn: dict[str, str]
    python: dict[str, str]
    torch: list[str]
    pip_pkgs: list[str]


TEST_MONOGENS: list[MonoGen] = [
    MonoGen(
        id=0,
        cuda={'12.4': '12.4.1_550.54.15'},
        cudnn={'9': '9.1.0.70'},
        python={'3.12': '3.12.6'},
        torch=['2.4.1', '2.6.0.dev20240918'],
        pip_pkgs=['cog==0.9.23', 'opencv-python==4.10.0.84'],
    ),
]

# Generations are immutable
# Never edit an existing one in place
# Always create a new one for any change
# Run after adding generation X:
# ./update.sh --min-gen-id=X
PROD_MONOGENS: list[MonoGen] = [
    MonoGen(
        id=0,
        cuda={
            '11.8': '11.8.0_520.61.05',
            '12.1': '12.1.1_530.30.02',
            '12.4': '12.4.1_550.54.15',
        },
        cudnn={
            '8': '8.9.7.29',
            '9': '9.1.0.70',
        },
        python={
            '3.8': '3.8.20',
            '3.9': '3.9.20',
            '3.10': '3.10.15',
            '3.11': '3.11.10',
            '3.12': '3.12.6',
        },
        torch=[
            '2.0.0',
            '2.0.1',
            '2.1.0',
            '2.1.1',
            '2.1.2',
            '2.2.0',
            '2.2.1',
            '2.2.2',
            '2.3.0',
            '2.3.1',
            '2.4.0',
            '2.4.1',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/refs/heads/add-waiting-env.zip',
            'opencv-python==4.10.0.84',
        ],
    ),
    MonoGen(
        id=1,
        cuda={
            '11.8': '11.8.0_520.61.05',
            '12.1': '12.1.1_530.30.02',
            '12.4': '12.4.1_550.54.15',
        },
        cudnn={
            '8': '8.9.7.29',
            '9': '9.1.0.70',
        },
        python={
            '3.8': '3.8.20',
            '3.9': '3.9.20',
            '3.10': '3.10.15',
            '3.11': '3.11.10',
            '3.12': '3.12.6',
        },
        torch=[
            '2.0.0',
            '2.0.1',
            '2.1.0',
            '2.1.1',
            '2.1.2',
            '2.2.0',
            '2.2.1',
            '2.2.2',
            '2.3.0',
            '2.3.1',
            '2.4.0',
            '2.4.1',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/refs/heads/add-waiting-env.zip',
            'opencv-python==4.10.0.84',
        ],
    ),
    MonoGen(
        id=2,
        cuda={
            '11.8': '11.8.0_520.61.05',
            '12.1': '12.1.1_530.30.02',
            '12.4': '12.4.1_550.54.15',
        },
        cudnn={
            '8': '8.9.7.29',
            '9': '9.1.0.70',
        },
        python={
            '3.8': '3.8.20',
            '3.9': '3.9.20',
            '3.10': '3.10.15',
            '3.11': '3.11.10',
            '3.12': '3.12.6',
        },
        torch=[
            '2.0.0',
            '2.0.1',
            '2.1.0',
            '2.1.1',
            '2.1.2',
            '2.2.0',
            '2.2.1',
            '2.2.2',
            '2.3.0',
            '2.3.1',
            '2.4.0',
            '2.4.1',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/a522a0f90600fbf8004f7748ca6bada5a3878a3e.zip',
            'opencv-python==4.10.0.84',
        ],
    ),
    MonoGen(
        id=3,
        cuda={
            '11.8': '11.8.0_520.61.05',
            '12.1': '12.1.1_530.30.02',
            '12.4': '12.4.1_550.54.15',
        },
        cudnn={
            '8': '8.9.7.29',
            '9': '9.1.0.70',
        },
        python={
            '3.8': '3.8.20',
            '3.9': '3.9.20',
            '3.10': '3.10.15',
            '3.11': '3.11.10',
            '3.12': '3.12.6',
        },
        torch=[
            '2.0.0',
            '2.0.1',
            '2.1.0',
            '2.1.1',
            '2.1.2',
            '2.2.0',
            '2.2.1',
            '2.2.2',
            '2.3.0',
            '2.3.1',
            '2.4.0',
            '2.4.1',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/4598529b07c620fd3a1d7e01746cf02ff5a641ef.zip',
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
                assert '==' in p or '@' in p, f'PIP package {p} is not pinned'


validate()
