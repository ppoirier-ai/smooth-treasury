from typing import Dict, Callable
import threading
import time
from common.exchange.client import ExchangeClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

class PriceMonitor:
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.running = False
        self.symbols: Dict[str, float] = {}  # symbol -> price
        self.callbacks: Dict[str, list[Callable]] = {}  # symbol -> [callback]
        self.exchange = ExchangeClient('', '')  # Public API access only
        self._thread = None
    
    def add_symbol(self, symbol: str, callback: Callable[[str, float], None] = None):
        """Add symbol to monitor."""
        self.symbols[symbol] = 0.0
        if callback:
            if symbol not in self.callbacks:
                self.callbacks[symbol] = []
            self.callbacks[symbol].append(callback)
    
    def remove_symbol(self, symbol: str):
        """Remove symbol from monitoring."""
        self.symbols.pop(symbol, None)
        self.callbacks.pop(symbol, None)
    
    def start(self):
        """Start price monitoring."""
        if self.running:
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Stop price monitoring."""
        self.running = False
        if self._thread:
            self._thread.join()
            self._thread = None
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                for symbol in list(self.symbols.keys()):
                    price = self.exchange.get_ticker(symbol)
                    if price:
                        old_price = self.symbols[symbol]
                        self.symbols[symbol] = price
                        
                        # Notify callbacks if price changed
                        if price != old_price and symbol in self.callbacks:
                            for callback in self.callbacks[symbol]:
                                try:
                                    callback(symbol, price)
                                except Exception as e:
                                    logger.error(f"Error in price callback: {str(e)}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in price monitoring: {str(e)}")
                time.sleep(self.update_interval) 