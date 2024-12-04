#!/usr/bin/env bash
# NOTE: This file is not used in Replicate production, as that environment requires a few
# other steps to happen between the sourcing of 'activate.sh' and exec'ing the next
# command.
set -euo pipefail

# shellcheck disable=SC1091
. /opt/r8/monobase/activate.sh
exec "$@"
