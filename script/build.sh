#!/bin/bash

# Build production images

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
docker build --tag monobase:latest --platform=linux/amd64 .
