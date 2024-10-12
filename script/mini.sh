#!/bin/bash

# Build mini image for testing

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
docker build --file mini.Dockerfile --tag monobase:mini --platform=linux/amd64 .