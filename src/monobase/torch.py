from dataclasses import dataclass
from typing import Optional

from monobase.util import Version


@dataclass(frozen=True, order=True)
class TorchSpec:
    python_min: Version
    python_max: Version
    cudas: list[str]


@dataclass(frozen=True, order=True)
class TorchDeps:
    torchaudio: str
    torchvision: str


# https://github.com/pytorch/pytorch/blob/main/RELEASE.md#release-compatibility-matrix
# See: Minimum Required Driver Version for CUDA Minor Version Compatibility
# https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html
torch_specs_dict = {
    # Releases
    '2.7': ('3.9', '3.13', ['cpu', '11.8', '12.6', '12.8']),
    '2.6': ('3.9', '3.13', ['cpu', '11.8', '12.4', '12.6']),
    '2.5': ('3.9', '3.12', ['cpu', '11.8', '12.1', '12.4']),
    '2.4': ('3.8', '3.12', ['cpu', '11.8', '12.1', '12.4']),
    '2.3': ('3.8', '3.11', ['cpu', '11.8', '12.1']),
    '2.2': ('3.8', '3.11', ['cpu', '11.8', '12.1']),
    '2.1': ('3.8', '3.11', ['cpu', '11.8', '12.1']),
    '2.0': ('3.8', '3.11', ['cpu', '11.7', '11.8']),
}

torch_deps_dict = {
    # Releases
    '2.7.1': TorchDeps('2.7.1', '0.22.1'),
    '2.7.0': TorchDeps('2.7.0', '0.22.0'),
    '2.6.0': TorchDeps('2.6.0', '0.21.0'),
    '2.5.1': TorchDeps('2.5.1', '0.20.1'),
    '2.5.0': TorchDeps('2.5.0', '0.20.0'),
    '2.4.1': TorchDeps('2.4.1', '0.19.1'),
    '2.4.0': TorchDeps('2.4.0', '0.19.0'),
    '2.3.1': TorchDeps('2.3.1', '0.18.1'),
    '2.3.0': TorchDeps('2.3.0', '0.18.0'),
    '2.2.2': TorchDeps('2.2.2', '0.17.2'),
    '2.2.1': TorchDeps('2.2.1', '0.17.1'),
    '2.2.0': TorchDeps('2.2.0', '0.17.0'),
    '2.1.2': TorchDeps('2.1.2', '0.16.2'),
    '2.1.1': TorchDeps('2.1.1', '0.16.1'),
    '2.1.0': TorchDeps('2.1.0', '0.16.0'),
    '2.0.1': TorchDeps('2.0.2', '0.15.2'),
    '2.0.0': TorchDeps('2.0.0', '0.15.0'),
}

_torch_specs: dict[Version, TorchSpec] = dict(
    (Version.parse(k), TorchSpec(Version.parse(pmin), Version.parse(pmax), cudas))
    for k, (pmin, pmax, cudas) in torch_specs_dict.items()
)

torch_deps: dict[Version, TorchDeps] = dict(
    (Version.parse(k), v) for k, v in torch_deps_dict.items()
)


def get_torch_spec(version: Version) -> Optional[TorchSpec]:
    # Check full version first, e.g. nightly
    spec = _torch_specs.get(version)
    if spec is None:
        # Fall back to major.minor
        spec = _torch_specs.get(Version.parse(f'{version.major}.{version.minor}'))
    return spec
