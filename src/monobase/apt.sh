#!/bin/bash

set -euo pipefail

# Install APT packages and bundle installed files into a tarball

if [ $# -le 1 ]; then
    echo "Usage $(basename "$0") <TARBALL> [PKG]..."
    exit 1
fi

tarball=$1
shift

# Disable post install clean so we can access downloaded .deb files
mv /etc/apt/apt.conf.d/docker-clean{,.skip}

# We need ar from binutils and compression codes used by various packages
apt-get update
apt-get install -y binutils bzip2 xz-utils zstd "$@"

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

# /src should be a bind mount to working directory to expose the tarball
cd /tmp/apt-root
tar -cvf "$tarball" --zstd .

rm -rf /tmp/apt-temp /tmp/apt-root

# Clean up and restore conf
rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin
mv /etc/apt/apt.conf.d/docker-clean{.skip,}
