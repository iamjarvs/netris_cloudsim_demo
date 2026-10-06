#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3 || echo "python3")"

echo "====================================================================="
echo "   Netris Spectrum-X CloudSim AI Fabric Dynamic Deployer"
echo "====================================================================="

LAST_DEPLOY_FILE="$SCRIPT_DIR/.last_deploy_dir"
rm -f "$LAST_DEPLOY_FILE"

# Run the deployment and collision avoidance engine (prepares workspace and variables)
$PYTHON_BIN "$SCRIPT_DIR/deploy-demo-fabric.py" --no-tofu "$@"
if [ -f "$LAST_DEPLOY_FILE" ]; then
    TARGET_DIR="$(cat "$LAST_DEPLOY_FILE")"
    if [ -d "$TARGET_DIR" ]; then
        echo ""
        echo "====================================================================="
        echo "Entering generated workspace: $TARGET_DIR"
        echo "====================================================================="
        cd "$TARGET_DIR"

        # Determine binary (tofu or terraform)
        TOFU_BIN="$(which tofu || which terraform || echo "tofu")"

        echo ""
        echo "====================================================================="
        echo "[*] Executing in $(pwd): $TOFU_BIN init"
        echo "====================================================================="
        "$TOFU_BIN" init

        echo ""
        echo "====================================================================="
        echo "[*] Executing in $(pwd): $TOFU_BIN plan"
        echo "====================================================================="
        "$TOFU_BIN" plan

        echo ""
        echo "====================================================================="
        echo "[✓] Switched to $TARGET_DIR. You can now run '$TOFU_BIN apply'."
        echo "====================================================================="
        exec bash -i
    fi
fi

