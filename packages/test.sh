#!/bin/bash

# Test wheel files produced by package scripts

if [ $# -lt 2 ]; then
    echo "Usage: $(basename "$0") <SCRIPT> <WHEEL>..."
    exit 1
fi

script="$1"
shift

# Install wheel files in the user layer
# This should detect any dependency conflicts
for whl in "$@"; do
    echo "$whl" >> /tmp/requirements.txt
done
/opt/r8/monobase/run.sh monobase.user --requirements /tmp/requirements.txt

# Activate the environment including Cog, monobase, and user venv
# shellcheck disable=SC1091
source /opt/r8/monobase/activate.sh

# Run the test script
python3 -c "$script"
echo "PASS: $script"
