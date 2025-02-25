from typing import Dict, Optional
from common.database.models import Bot, Client, Trade
from common.exchange.client import ExchangeClient
from common.bot.grid_bot import GridBot
from common.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

class BotService:
    def __init__(self):
        self.active_bots: Dict[int, GridBot] = {}
    
    def start_bot(self, bot: Bot, client: Client) -> bool:
        """Start a grid trading bot."""
        try:
            # Create exchange client
            exchange = ExchangeClient(client.api_key, client.api_secret)
            
            # Create and start grid bot
            grid_bot = GridBot(
                bot_id=bot.bot_id,
                client=exchange,
                pair=bot.pair,
                lower=bot.lower_price,
                upper=bot.upper_price,
                grids=bot.grids,
                capital=bot.capital_btc
            )
            grid_bot.start()
            
            # Store active bot
            self.active_bots[bot.bot_id] = grid_bot
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot {bot.bot_id}: {str(e)}")
            return False
    
    def stop_bot(self, bot_id: int) -> bool:
        """Stop a grid trading bot."""
        try:
            if bot_id in self.active_bots:
                self.active_bots[bot_id].stop()
                del self.active_bots[bot_id]
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            return False
    
    def get_bot_status(self, bot_id: int) -> Optional[dict]:
        """Get current bot status."""
        if bot_id not in self.active_bots:
            return None
            
        bot = self.active_bots[bot_id]
        return {
            'bot_id': bot.bot_id,
            'pair': bot.pair,
            'active_orders': len(bot.orders),
            'capital': bot.capital
        } 