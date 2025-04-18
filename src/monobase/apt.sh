#!/bin/bash

set -euo pipefail

# Install APT + third party packages and bundle installed files into a tarball

if [ $# -le 1 ]; then
    echo "Usage $(basename "$0") <TARBALL> [PKG]..."
    exit 1
fi

tarball=$1

prefix=/tmp/apt-root
shift

##############################
# Package specific scripts
##############################

_gh_latest_assets() {
    curl -fsSL "https://api.github.com/repos/$1/releases/latest" | jq --raw-output '.assets[].browser_download_url'
}

install_s5cmd() {
    url="$(_gh_latest_assets peak/s5cmd | grep Linux-64bit.tar.gz)"
    mkdir -p "$prefix/usr/bin"
    curl -fsSL "$url" | tar -xzf - -C "$prefix/usr/bin" s5cmd
}

##############################
# Main script
##############################

# Split packages into APTs and third party ones
apts=()
pkgs=()
for p in "$@"; do
    if declare -F "install_$p" &> /dev/null; then
        pkgs+=("$p")
    else
        apts+=("$p")
    fi
done

mkdir -p "$prefix"

if [ ${#apts[@]} -ge 1 ]; then
    echo "Installing APT packages ${apts[*]}"
    apt-get update
    apt-get install --yes --download-only "${apts[@]}"
    find /var/cache/apt/archives -type f -name "*.deb" -print0 | while IFS= read -r -d '' f; do
        tmp="$(mktemp -d -t monobase.XXXXXXXX)"
        cd "$tmp"
        # Each .deb file contains 3 files
        # debian-binary
        # control.tar.*
        # data.tar.*
        # We only care about the data file

        # Extract the .deb file
        echo "Extracting files from $f..."
        ar x "$f"

        # Extract the data file
        tar -xf data.tar.* -C "$prefix"
        rm -rf "$tmp"
    done

    # Clean up
    rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin
fi

if [ ${#pkgs[@]} -ge 1 ]; then
    echo "Installing third-party packages ${pkgs[*]}"
    for p in "${pkgs[@]}"; do
        "install_$p"
    done
fi

# tarball should be in a working directory bind mount to expose it to the host
/opt/r8/monobase/tar.sh "$tarball" "$prefix" .

rm -rf "$prefix"
