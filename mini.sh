#!/bin/bash

# Build mini image for testing

set -euo pipefail

docker build --file mini.Dockerfile --tag monobase:mini --platform=linux/amd64 .
