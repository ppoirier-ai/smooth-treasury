#!/bin/bash
# Set the configuration path
export CONFIG_PATH=$(pwd)/config/dev_config.yaml

# Remove old database if exists
if [ -f "./grid_bot.db" ]; then
    echo "Removing old database..."
    rm ./grid_bot.db
fi

# Initialize database
python -m scripts.init_db

# Run the command
python -m cli.main "$@" 