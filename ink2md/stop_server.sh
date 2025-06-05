#!/bin/bash

# Define the PID directory
PID_DIR=".pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
# We won't strictly rely on the frontend PID file for killing,
# but we'll still clean it up.
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# Function to stop a process given its PID file and name
stop_process() {
  local pid_file=$1
  local process_name=$2

  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")

    if [ -n "$pid" ] && ps -p "$pid" > /dev/null; then
      echo "Attempting to stop $process_name (PID $pid)..."
      kill "$pid" # Send TERM
      sleep 2

      if ps -p "$pid" > /dev/null; then
        echo "$process_name (PID $pid) did not stop gracefully. Forcing termination..."
        kill -9 "$pid" # Send KILL
        sleep 1
      fi

      if ! ps -p "$pid" > /dev/null; then
        echo "$process_name (PID $pid) has been stopped."
        rm "$pid_file"
      else
        echo "Error: Could not stop $process_name (PID $pid)."
      fi
    else
      echo "$process_name PID file found, but no process with PID $pid is running. Removing PID file."
      rm "$pid_file"
    fi
  else
    echo "$process_name PID file not found. It might already be stopped or the file was removed."
  fi
}

# Function to stop the frontend using pkill
stop_frontend() {
  local process_name="Frontend server (Vite/Node)"
  # Use a pattern that specifically matches your Vite process based on your ps output
  # Adjust this pattern if necessary to be more specific to your project.
  local pattern="node .*vite.*ink2md"

  echo "Attempting to find and stop $process_name matching '$pattern'..."
  
  # Find PIDs matching the pattern
  pids=$(pgrep -f "$pattern")

  if [ -n "$pids" ]; then
    echo "Found PIDs: $pids. Sending TERM signal..."
    pkill -f "$pattern" # Sends SIGTERM by default
    sleep 3

    # Check if any are still running
    pids=$(pgrep -f "$pattern")
    if [ -n "$pids" ]; then
        echo "Some frontend processes ($pids) did not stop gracefully. Forcing termination..."
        pkill -9 -f "$pattern" # Sends SIGKILL
        sleep 1
    fi

    # Final check
    pids=$(pgrep -f "$pattern")
    if [ -z "$pids" ]; then
        echo "$process_name has been stopped."
        # Clean up the old PID file if it exists
        if [ -f "$FRONTEND_PID_FILE" ]; then
            rm "$FRONTEND_PID_FILE"
        fi
    else
        echo "Error: Could not stop all frontend processes ($pids)."
    fi
  else
    echo "$process_name not found running."
    # Clean up the old PID file if it exists
    if [ -f "$FRONTEND_PID_FILE" ]; then
        echo "Removing stale PID file."
        rm "$FRONTEND_PID_FILE"
    fi
  fi
}


# Stop the backend server (using the original method)
stop_process "$BACKEND_PID_FILE" "Backend server"

# Stop the frontend server (using the new method)
stop_frontend

# Optional: Attempt to remove the .pids directory if it's empty
if [ -d "$PID_DIR" ] && [ -z "$(ls -A $PID_DIR)" ]; then
  echo "Removing empty PID directory: $PID_DIR"
  rmdir "$PID_DIR"
fi

echo "Stop script execution finished."