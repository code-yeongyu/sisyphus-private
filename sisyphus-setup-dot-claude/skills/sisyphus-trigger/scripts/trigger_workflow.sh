#!/usr/bin/env bash
# Trigger the sisyphus-work workflow on GitHub Actions
# Usage: trigger_workflow.sh <branch_name>

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Error: Branch name required"
    echo "Usage: $0 <branch_name>"
    exit 1
fi

BRANCH_NAME="$1"

echo "🚀 Triggering GitHub Actions workflow for branch: $BRANCH_NAME"

gh workflow run trigger-sisyphus-work.yml \
    -f branch_name="$BRANCH_NAME"

echo "✅ Workflow triggered successfully!"
echo "📊 Check status: gh run list --workflow=trigger-sisyphus-work.yml"
