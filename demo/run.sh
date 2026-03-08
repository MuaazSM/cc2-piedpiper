#!/bin/bash

# Lorri AI Terminal Demo Runner
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  Lorri AI — Terminal Demo"
echo "  Team Jugaadus · CyberCypher R2"
echo "=========================================="
echo ""
echo "Choose a demo:"
echo "  1) Full Walkthrough (Interactive, step-by-step with pauses)"
echo "  2) Quick Demo (Fast, no pauses)"
echo "  3) Benchmark Only (Solomon VRPTW validation)"
echo ""

read -p "Enter choice (1-3): " choice

cd "$PROJECT_ROOT"

case $choice in
    1)
        echo "Starting Full Walkthrough..."
        PYTHONPATH="$PROJECT_ROOT" python -m demo.terminal_presenter
        ;;
    2)
        echo "Starting Quick Demo..."
        PYTHONPATH="$PROJECT_ROOT" python -c "
import os, sys
sys.path.insert(0, '.')
os.environ.setdefault('GOOGLE_API_KEY', '')
from demo.terminal_presenter import (
    TerminalPresenter, PipelineState, load_env_file,
    demo_observe, demo_reason, demo_decide, demo_act,
    demo_insight, demo_learn, demo_final_summary
)
from backend.app.db.base import Base
from backend.app.db.session import engine
import backend.app.models
Base.metadata.create_all(bind=engine)
load_env_file()
p = TerminalPresenter(slow_mode=False)
s = PipelineState()
demo_observe(p, s)
demo_reason(p, s)
demo_decide(p, s)
demo_act(p, s)
demo_insight(p, s)
demo_learn(p, s)
demo_final_summary(p, s)
"
        ;;
    3)
        echo "Starting Benchmark Validation..."
        PYTHONPATH="$PROJECT_ROOT" python -c "
import os, sys
sys.path.insert(0, '.')
from demo.terminal_presenter import TerminalPresenter, load_env_file, demo_solomon_benchmark
from backend.app.db.base import Base
from backend.app.db.session import engine
import backend.app.models
Base.metadata.create_all(bind=engine)
load_env_file()
p = TerminalPresenter(slow_mode=True)
demo_solomon_benchmark(p)
"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac