#!/bin/sh
# Analyzes the messy inventory (orphan volume -> exit 2), then the tidy one (exit 0).
set -u
export PYTHONPATH="$(dirname "$0")/src"

echo "=== Analyzing samples/messy-inventory.json ==="
python3 -m oci_block_volume_orphan_detector samples/messy-inventory.json
echo "exit code: $? (2 = orphan volume found, expected for the messy inventory)"
echo
echo "=== Analyzing samples/tidy-inventory.json ==="
python3 -m oci_block_volume_orphan_detector samples/tidy-inventory.json
echo "exit code: $? (0 = no orphans, expected for the tidy inventory)"
