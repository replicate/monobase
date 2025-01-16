#!/bin/bash

set -euo pipefail

# Install APT packages and bundle installed files into a tarball

if [ $# -le 1 ]; then
    echo "Usage $(basename "$0") <TARBALL> [PKG]..."
    exit 1
fi

tarball=$1
shift

apt-get update
apt-get install --yes --download-only "$@"

mkdir /tmp/apt-temp /tmp/apt-root

cd /tmp/apt-temp
find /var/cache/apt/archives -type f -name "*.deb" -print0 | while IFS= read -r -d '' f; do
    # Each .deb file contains 3 files
    # debian-binary
    # control.tar.*
    # data.tar.*
    # We only care about the data file

    # Extract the .deb file
    echo "Extracting files from $f..."
    ar x "$f"

    # Extract the data file
    tar -xf data.tar.* -C /tmp/apt-root
    rm ./*
done

# tarball should be in a working directory bind mount to expose it to the host
/opt/r8/monobase/tar.sh "$tarball" /tmp/apt-root .

rm -rf /tmp/apt-temp /tmp/apt-root

# Clean up
rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin
