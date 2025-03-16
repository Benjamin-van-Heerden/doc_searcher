#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"

# Check for running instances and kill them if they exist
PROCESS_NAME="doc_searcher.py"
RUNNING_PID=$(pgrep -f "$PROCESS_NAME")
if [ -n "$RUNNING_PID" ]; then
    echo "Found existing process(es) running. Killing them..."
    pkill -f "$PROCESS_NAME"
    sleep 1  # Give processes time to terminate
fi

# Activate virtual environment and run program
source .venv/bin/activate
# crawl4ai-setup # this requires admin privileges - run once as root before starting the server
uv run doc_searcher.py
