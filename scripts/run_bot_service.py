#!/usr/bin/env python
"""
Bot service runner script.
This keeps the bot running until manually stopped with Ctrl+C.
"""
import sys
import os
import time
import signal
import logging
import pathlib

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up configuration path
root_dir = pathlib.Path(__file__).parent.parent.absolute()
os.environ['CONFIG_PATH'] = str(root_dir / 'config' / 'dev_config.yaml')

from common.database.connection import get_session
from common.database.models import Bot, Client
from common.services.bot_service import BotService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the bot service."""
    if len(sys.argv) < 4:
        print("Usage: python run_bot_service.py <client_id> <pair> <capital>")
        sys.exit(1)
    
    client_id = int(sys.argv[1])
    pair = sys.argv[2]
    capital = float(sys.argv[3])
    
    # Print configuration for debugging
    print(f"Using config: {os.environ.get('CONFIG_PATH')}")
    
    bot_service = BotService()
    session = get_session()
    
    try:
        client = session.query(Client).filter_by(client_id=client_id).first()
        if not client:
            logger.error(f"Client {client_id} not found")
            sys.exit(1)
            
        bot = session.query(Bot).filter(
            Bot.client_id == client_id,
            Bot.pair == pair
        ).first()
        
        if not bot:
            logger.error(f"No bot configuration found for client {client_id} and pair {pair}")
            sys.exit(1)
            
        # Update bot status and capital
        bot.status = 'active'
        bot.capital_btc = capital
        session.commit()
        
        # Start the bot
        if bot_service.start_bot(bot, client):
            logger.info(f"Bot started: client={client_id} pair={pair} capital={capital}BTC")
            logger.info("Press Ctrl+C to stop")
            
            # Setup signal handling for graceful shutdown
            def signal_handler(sig, frame):
                logger.info("Stopping bot...")
                bot_service.stop_bot(bot.bot_id)
                bot.status = 'stopped'
                session.commit()
                logger.info("Bot stopped")
                sys.exit(0)
                
            signal.signal(signal.SIGINT, signal_handler)
            
            # Keep process alive
            while True:
                time.sleep(1)
        else:
            bot.status = 'error'
            session.commit()
            logger.error("Failed to start bot")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main() 