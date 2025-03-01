#!/bin/bash
# Set the configuration path
export CONFIG_PATH=$(pwd)/config/dev_config.yaml

# Only remove database if --reset flag is provided
if [ "$1" = "--reset" ]; then
    echo "Resetting database..."
    if [ -f "./grid_bot.db" ]; then
        rm ./grid_bot.db
    fi
    # Initialize database
    python -m scripts.init_db
    shift # Remove the --reset argument
else
    # Initialize database only if it doesn't exist
    if [ ! -f "./grid_bot.db" ]; then
        echo "Database not found. Initializing..."
        python -m scripts.init_db
    fi
fi

# Run the command
python -m cli.main "$@"

chmod +x scripts/test_exchange.py 