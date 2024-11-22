from dataclasses import dataclass

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
torch_specs_dict = {
    # Nightly with a subset of Python and CUDA combinations
    '2.6': ('3.11', '3.12', ['12.4']),
    # Releases
    '2.5': ('3.9', '3.12', ['11.8', '12.1', '12.4']),
    '2.4': ('3.8', '3.12', ['11.8', '12.1', '12.4']),
    '2.3': ('3.8', '3.11', ['11.8', '12.1']),
    '2.2': ('3.8', '3.11', ['11.8', '12.1']),
    '2.1': ('3.8', '3.11', ['11.8', '12.1']),
    '2.0': ('3.8', '3.11', ['11.7', '11.8']),
}

torch_deps_dict = {
    # Nightly
    '2.6.0.dev20240918': TorchDeps('2.5.0.dev20240918', '0.20.0.dev20240918'),
    # Releases
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

torch_specs: dict[Version, TorchSpec] = dict(
    (Version.parse(k), TorchSpec(Version.parse(pmin), Version.parse(pmax), cudas))
    for k, (pmin, pmax, cudas) in torch_specs_dict.items()
)

torch_deps: dict[Version, TorchDeps] = dict(
    (Version.parse(k), v) for k, v in torch_deps_dict.items()
)
