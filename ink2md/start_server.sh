#!/bin/bash

# Create a directory for PIDs if it doesn't exist
mkdir -p .pids

# Get the absolute directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Source conda.sh to enable conda command
source ~/miniconda3/etc/profile.d/conda.sh

# Activate the nlp environment and make sure it's available to subprocesses
conda activate nlp

# Export all necessary environment variables
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"
export PATH="/home/$USER/miniconda3/envs/nlp/bin:$PATH"
export PYTHONUNBUFFERED=1

# Start the Flask backend
cd "$SCRIPT_DIR"
nohup python3 app.py > backend.log 2>&1 &
backend_pid=$!
disown $backend_pid
echo $backend_pid > .pids/backend.pid
echo "Backend server started on port 6201 with PID $backend_pid"

# Start the Vite frontend
cd "$SCRIPT_DIR"
nohup npm run dev > frontend.log 2>&1 &
frontend_pid=$!
disown $frontend_pid
echo $frontend_pid > .pids/frontend.pid
echo "Frontend server started with PID $frontend_pid"