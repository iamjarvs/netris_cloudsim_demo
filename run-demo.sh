#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3 || echo "python3")"

echo "====================================================================="
echo "   Netris Spectrum-X CloudSim AI Fabric Dynamic Deployer"
echo "====================================================================="

# Run the deployment and collision avoidance engine
$PYTHON_BIN "$SCRIPT_DIR/deploy-demo-fabric.py" "$@"

