from collections import namedtuple

from util import Version


TorchSpec = namedtuple('TorchSpec', ['python_min', 'python_max', 'cudas'])
TorchDeps = namedtuple('TorchDeps', ['torchaudio', 'torchvision'])

# https://github.com/pytorch/pytorch/blob/main/RELEASE.md#release-compatibility-matrix
torch_specs_dict = {
    '2.5': ('3.9', '3.12', ['11.8', '12.1', '12.4']),
    '2.4': ('3.8', '3.12', ['11.8', '12.1', '12.4']),
    '2.3': ('3.8', '3.11', ['11.8', '12.1']),
    '2.2': ('3.8', '3.11', ['11.8', '12.1']),
    '2.1': ('3.8', '3.11', ['11.8', '12.1']),
    '2.0': ('3.8', '3.11', ['11.7', '11.8']),
}

torch_deps_dict = {
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

torch_deps: dict[Version, TorchSpec] = dict(
    (Version.parse(k), v) for k, v in torch_deps_dict.items())
