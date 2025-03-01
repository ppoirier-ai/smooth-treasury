import click
from typing import Optional
from common.database.connection import get_session
from common.database.models import Bot, Client
from common.utils.logger import setup_logger
from common.services.bot_service import BotService

logger = setup_logger(__name__)

# Create global bot service instance
bot_service = BotService()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--pair', type=str, required=True, help='Trading pair (e.g., BTC/SOL)')
@click.option('--lower', type=float, required=True, help='Lower price bound')
@click.option('--upper', type=float, required=True, help='Upper price bound')
@click.option('--grids', type=int, required=True, help='Number of grid lines')
def configure_bot(client_id: int, pair: str, lower: float, upper: float, grids: int):
    """Configure a new grid trading bot."""
    session = get_session()
    try:
        # Verify client exists
        client = session.query(Client).filter_by(client_id=client_id).first()
        if not client:
            raise click.ClickException(f"Client {client_id} not found")

        # Create bot configuration
        bot = Bot(
            client_id=client_id,
            pair=pair,
            status='configured',
            lower_price=lower,
            upper_price=upper,
            grids=grids,
            capital_btc=0.0  # Initialize with 0
        )
        session.add(bot)
        session.commit()
        click.echo(f"Bot configured: client={client_id}, pair={pair}")

    except Exception as e:
        logger.error(f"Failed to configure bot: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--pair', type=str, required=True, help='Trading pair')
@click.option('--capital', type=float, required=True, help='Trading capital in BTC')
@click.option('--daemon', is_flag=True, help='Run in daemon mode')
def start_bot(client_id: int, pair: str, capital: float, daemon: bool = False):
    """Start a grid trading bot."""
    session = get_session()
    try:
        client = session.query(Client).filter_by(client_id=client_id).first()
        if not client:
            raise click.ClickException(f"Client {client_id} not found")
            
        bot = session.query(Bot).filter(
            Bot.client_id == client_id,
            Bot.pair == pair
        ).first()
        
        if not bot:
            raise click.ClickException(f"No bot configuration found for client {client_id} and pair {pair}")
            
        # Update bot status and capital
        bot.status = 'active'
        bot.capital_btc = capital
        session.commit()
        
        # Start the bot
        if bot_service.start_bot(bot, client):
            # If daemon mode, detach and keep running
            if daemon:
                import threading
                import time
                
                def keep_alive():
                    """Keep the process alive."""
                    try:
                        click.echo(f"Bot running in daemon mode. Press Ctrl+C to stop.")
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        click.echo("Stopping bot...")
                        bot_service.stop_bot(bot.bot_id)
                        
                # Start background thread to keep process alive
                thread = threading.Thread(target=keep_alive)
                thread.daemon = False
                thread.start()
                thread.join()  # Wait for keyboard interrupt
            else:
                click.echo(f"Bot started: client={client_id} pair={pair} capital={capital}BTC")
                click.echo("Note: Bot will stop when this command exits. Use --daemon to keep running.")
        else:
            bot.status = 'error'
            session.commit()
            raise click.ClickException("Failed to start bot")
    
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--pair', type=str, required=True, default='BTC/SOL', help='Trading pair')
def stop_bot(client_id: int, pair: str):
    """Stop a running grid trading bot."""
    session = get_session()
    try:
        bot = session.query(Bot).filter(
            Bot.client_id == client_id,
            Bot.pair == pair
        ).first()

        if not bot:
            raise click.ClickException(f"No bot found for client {client_id} and pair {pair}")

        if bot.status != 'active':
            raise click.ClickException(f"Bot is not active")

        # Stop the bot using service
        if bot_service.stop_bot(bot.bot_id):
            bot.status = 'stopped'
            session.commit()
            click.echo(f"Bot stopped: client={client_id} pair={pair}")
        else:
            raise click.ClickException("Failed to stop bot")

    except Exception as e:
        logger.error(f"Failed to stop bot: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close() 