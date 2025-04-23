#!/bin/bash

# Test wheel files produced by package scripts

if [ $# -ne 2 ]; then
    echo "Usage: $(basename "$0") <REQUIREMENTS> <SCRIPT>"
    exit 1
fi

/opt/r8/monobase/run.sh monobase.user --requirements "$1"

# Activate the environment including Cog, monobase, and user venv
# shellcheck disable=SC1091
source /opt/r8/monobase/activate.sh

# Run the test script
python3 -c "$2"
echo "PASS: $2"
