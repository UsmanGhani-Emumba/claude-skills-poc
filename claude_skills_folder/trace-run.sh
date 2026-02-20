#!/bin/bash
# =============================================================================
# trace-run.sh — Run a Claude Code skill with full stream-json tracing
# =============================================================================
# Usage:
#   bash trace-run.sh "/research How to remember things like a pro"
#   bash trace-run.sh "/pipeline Write about AI trends"
#
# Output:
#   - traces/<timestamp>-stream.jsonl   (full stream-json trace)
#   - traces/hooks-<session>.jsonl      (hooks log, created automatically)
#
# Note: Token counts and cost data only appear when using an API key.
#       On Pro subscription, these fields will show 0.
# =============================================================================

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: bash trace-run.sh \"<prompt>\""
    echo "Example: bash trace-run.sh \"/research How to remember things like a pro\""
    exit 1
fi

PROMPT="$*"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TRACE_FILE="traces/${TIMESTAMP}-stream.jsonl"

mkdir -p traces

echo "================================================"
echo "  Claude Code Trace Run"
echo "================================================"
echo "  Prompt:     $PROMPT"
echo "  Trace file: $TRACE_FILE"
echo "  Hook log:   traces/hooks-<session>.jsonl"
echo "================================================"
echo ""

claude -p "$PROMPT" \
    --output-format stream-json \
    --verbose \
    | tee "$TRACE_FILE"

echo ""
echo "================================================"
echo "  Trace complete!"
echo "  Stream trace saved to: $TRACE_FILE"
echo "================================================"
echo ""
echo "  Analyze with:"
echo "    python analyze-trace.py stream $TRACE_FILE"
echo "    python analyze-trace.py both latest"
