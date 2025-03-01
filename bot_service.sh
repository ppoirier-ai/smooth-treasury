#!/bin/bash
# Ensure we're using the right configuration
export CONFIG_PATH=$(pwd)/config/dev_config.yaml

# Run the bot service with the provided arguments
./scripts/run_bot_service.py "$@" 