#!/bin/bash

# Build production images

set -euo pipefail

docker build --tag monobase:latest --platform=linux/amd64 .
