#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3 || echo "python3")"

echo "====================================================================="
echo "   Netris Spectrum-X CloudSim AI Fabric Dynamic Deployer"
echo "====================================================================="

# Run the deployment and collision avoidance engine
$PYTHON_BIN "$SCRIPT_DIR/deploy-demo-fabric.py" "$@"

# Read the targeted directory created by the python script
LAST_DEPLOY_FILE="$SCRIPT_DIR/.last_deploy_dir"
if [ -f "$LAST_DEPLOY_FILE" ]; then
    TARGET_DIR="$(cat "$LAST_DEPLOY_FILE")"
    if [ -d "$TARGET_DIR" ]; then
        echo ""
        echo "====================================================================="
        echo "Entering generated workspace: $TARGET_DIR"
        echo "====================================================================="
        cd "$TARGET_DIR"
        exec bash -i
    fi
fi

