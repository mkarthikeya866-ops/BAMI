#!/bin/bash
# ============================================================
# BAMI Startup Script for macOS & Linux
# ============================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "============================================================"
echo " 🧬 Starting BAMI: Bioactive Molecule Intelligence Platform"
echo "============================================================"

# Check if .venv exists
if [ -d ".venv" ]; then
    echo "Activating Python virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating Python virtual environment (venv)..."
    source venv/bin/activate
fi

# If node is installed, use npm run dev
if command -v npm &> /dev/null; then
    echo "Starting Backend & Frontend via npm run dev..."
    npm run dev
else
    echo "Starting FastAPI Backend on http://0.0.0.0:8000..."
    python3 -m uvicorn app.main:app --app-dir Backend --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    echo "Starting Frontend Server on http://0.0.0.0:5501..."
    python3 -m http.server 5501 --directory Frontend &
    FRONTEND_PID=$!

    echo ""
    echo "🚀 Platform is running at: http://localhost:5501"
    echo "Press CTRL+C to stop both servers."
    echo ""
    
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
    wait
fi
