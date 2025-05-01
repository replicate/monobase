import logging
import os.path
from dataclasses import dataclass

from monobase.util import setup_logging

log = logging.getLogger(__name__)


@dataclass(frozen=True, order=True)
class MonoGen:
    id: int
    cuda: dict[str, str]
    cudnn: dict[str, str]
    python: dict[str, str]
    torch: list[str]
    pip_pkgs: list[str]

    @property
    def otel_attributes(self):
        return {f'monogen_{k}': str(v) for k, v in self.__dict__.items()}


# uv venv --seed does not install deprecated setuptools or wheel for Python 3.12
# Packaging is needed for flash-attn, etc.
# Explicitly declare them here
# Versions are not pinned and we will use whatever Torch index has
SEED_PKGS = ['pip', 'packaging', 'setuptools', 'wheel']

TEST_MONOGENS: list[MonoGen] = [
    MonoGen(
        id=0,
        cuda={'12.4': '12.4.1_550.54.15'},
        cudnn={'9': '9.1.0.70'},
        python={'3.12': '3.12.8'},
        torch=[
            '2.4.1',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=1,
        cuda={'12.4': '12.4.1_550.54.15'},
        cudnn={'9': '9.1.0.70'},
        python={'3.12': '3.12.8', '3.13': '3.13.1'},
        torch=[
            '2.4.1',
            '2.5.1',
        ],
        pip_pkgs=SEED_PKGS,
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/4598529b07c620fd3a1d7e01746cf02ff5a641ef.zip',
            'opencv-python==4.10.0.84',
        ],
    ),
    MonoGen(
        id=4,
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/2f883e462e0e0606e38a1d05ef5d02bfe43fa19e.zip',
            'opencv-python==4.10.0.84',
        ],
    ),
    MonoGen(
        id=5,
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/2f883e462e0e0606e38a1d05ef5d02bfe43fa19e.zip',
            'opencv-python==4.10.0.84',
            # seed packages
            'pip==24.2',
            'setuptools==75.1.0',
            'wheel==0.44.0',
        ],
    ),
    MonoGen(
        id=6,
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/2f883e462e0e0606e38a1d05ef5d02bfe43fa19e.zip',
        ]
        + SEED_PKGS,
    ),
    MonoGen(
        id=7,
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/0c3c6f18d0871cab0470ceb5301a550e85d61567.zip',
        ]
        + SEED_PKGS,
    ),
    MonoGen(
        id=8,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=[
            'cog @ https://github.com/replicate/cog/archive/0c3c6f18d0871cab0470ceb5301a550e85d61567.zip',
        ]
        + SEED_PKGS,
    ),
    MonoGen(
        id=9,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=10,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.12': '3.12.7',
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
            # NOTE(meatballhat): This is turned off until we can figure out how to handle
            # nightlies better since the torch package index only retains ~2 months of
            # versions:
            ## Nightly
            #'2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=11,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.12': '3.12.7',
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
            '2.6.0.dev20241121',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=12,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.12': '3.12.7',
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
            '2.5.0',
            '2.5.1',
            # Nightly
            '2.6.0.dev20241121',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=13,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.12': '3.12.7',
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
            '2.5.0',
            '2.5.1',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=14,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.9': '3.9.21',
            '3.10': '3.10.16',
            '3.11': '3.11.11',
            '3.12': '3.12.8',
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
            '2.5.0',
            '2.5.1',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=15,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.9': '3.9.21',
            '3.10': '3.10.16',
            '3.11': '3.11.11',
            '3.12': '3.12.8',
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
            '2.5.0',
            '2.5.1',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=16,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.9': '3.9.21',
            '3.10': '3.10.16',
            '3.11': '3.11.11',
            '3.12': '3.12.9',
            '3.13': '3.13.2',
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
            '2.5.0',
            '2.5.1',
            '2.6.0',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
    MonoGen(
        id=17,
        cuda={
            '11.7': '11.7.0_515.43.04',
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
            '3.9': '3.9.21',
            '3.10': '3.10.16',
            '3.11': '3.11.11',
            '3.12': '3.12.9',
            '3.13': '3.13.2',
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
            '2.5.0',
            '2.5.1',
            '2.6.0',
            # Nightly
            '2.6.0.dev20240918',
        ],
        pip_pkgs=SEED_PKGS,
    ),
]

MONOGENS: dict[str, list[MonoGen]] = {
    'test': TEST_MONOGENS,
    'prod': PROD_MONOGENS,
}


def validate() -> None:
    log.info('Validating monobase generations...')
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
                assert p in SEED_PKGS or '==' in p or '@' in p, (
                    f'PIP package {p} is not pinned'
                )
    for mg in MONOGENS['prod']:
        rdir = os.path.join(os.path.dirname(__file__), 'requirements', f'g{mg.id:05d}')
        if not os.path.exists(rdir):
            log.error(
                f'Missing monobase generation {mg.id}, did you forget to run script/update?'
            )
            raise IOError('Missing monobase generation')


if __name__ == '__main__':
    setup_logging()
    validate()
