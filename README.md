monobase
========

Mono cog base image with all CUDA + Python + Torch dependencies

### Design

* Prepare everything outside of `Dockerfile`
* Install CUDA & CuDNN from runfile and tarballs under `/usr/local/cuda`
* Install Python, Torch, etc. under `/usr/local/uv`
* Pre-compute `ld.so.cache` under `/usr/local/etc`

### Directory layout

```
/usr/local
├── bin  // uv, uvx
├── etc  // optimize.py
│  └── ld.so.cache.d
   │  ├── cuda11.7-cudnn9-python3.8
   │  ├── ...
   │  └── cuda12.4-cudnn9-python3.12
├── cuda // cuda.py
│  ├── cuda-11.7
│  ├── ...
│  ├── cuda-12.4
│  ├── cudnn-9-cuda11
│  └── cudnn-9-cuda12
└── uv   // uv.py
   ├── cache
   ├── python
   │  ├── cpython-3.8.20-linux-x86_64-gnu
   │  ├── ...
   │  └── cpython-3.12.6-linux-x86_64-gnu
   └── venv
      ├── python3.8-torch2.0.0-cu117
      ├── python3.8-torch2.0.0-cu118
      ├── ...
      ├── python3.12-torch2.4.1-cu118
      ├── python3.12-torch2.4.1-cu121
      └── python3.12-torch2.4.1-cu124
```
