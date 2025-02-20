#!/usr/bin/env bash

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

# Serve the API and don't shutdown the container
if [ "$SERVE_API_LOCALLY" == "true" ]; then
    echo "musicgen-worker: Starting RunPod Handler"
    python3 -u /app/handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    echo "musicgen-worker: Starting RunPod Handler"
    python3 -u /app/handler.py
fi