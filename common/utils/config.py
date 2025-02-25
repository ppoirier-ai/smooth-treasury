import os
import yaml
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """Load and return configuration from config.yaml."""
    config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        'database': {
            'url': os.getenv('DATABASE_URL'),
            'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '5')),
            'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', '10'))
        },
        'redis': {
            'url': os.getenv('REDIS_URL'),
            'db': int(os.getenv('REDIS_DB', '0'))
        },
        'rabbitmq': {
            'url': os.getenv('RABBITMQ_URL'),
            'exchange': os.getenv('RABBITMQ_EXCHANGE', 'gridbot')
        },
        'binance': {
            'testnet': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
            'timeout': int(os.getenv('BINANCE_TIMEOUT', '10000'))
        },
        'telegram': {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID')
        }
    } 