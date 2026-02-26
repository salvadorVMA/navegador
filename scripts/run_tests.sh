#!/usr/bin/env bash
# run_tests.sh — persistent test runner for Navegador
# Works from iPad: just type  bash scripts/run_tests.sh  in terminal.
#
# Usage:
#   bash scripts/run_tests.sh              # unit tests only (fast, ~10s)
#   bash scripts/run_tests.sh essays       # regenerate all 10 essays (needs OPENAI_API_KEY)
#   bash scripts/run_tests.sh all          # unit tests + essays

set -euo pipefail
cd "$(dirname "$0")/.."   # always run from repo root

MODE="${1:-unit}"

run_unit() {
    echo "=== Unit tests ==="
    python -m pytest tests/unit/test_ses_regression.py -v \
        2>&1 | tee /tmp/test_ses_regression.log
    echo "Log: /tmp/test_ses_regression.log"
}

run_essays() {
    echo "=== Essay tests (background, survives disconnect) ==="
    nohup python scripts/debug/run_essay_tests.py \
        > /tmp/essay_tests.log 2>&1 &
    echo "PID: $!"
    echo "Monitor:  tail -f /tmp/essay_tests.log"
    echo "Results:  data/results/essay_tests/"
}

case "$MODE" in
    unit)   run_unit ;;
    essays) run_essays ;;
    all)    run_unit; run_essays ;;
    *)      echo "Usage: bash scripts/run_tests.sh [unit|essays|all]"; exit 1 ;;
esac
