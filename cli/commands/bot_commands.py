import click
from typing import Optional
from common.database.connection import get_session
from common.database.models import Bot, Client
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--pair', type=str, required=True, default='BTC/SOL', help='Trading pair')
@click.option('--lower', type=float, required=True, help='Lower price bound')
@click.option('--upper', type=float, required=True, help='Upper price bound')
@click.option('--grids', type=int, required=True, help='Number of grid lines')
@click.option('--leverage', type=int, default=2, help='Leverage (default: 2x)')
def configure_bot(client_id: int, pair: str, lower: float, upper: float, grids: int, leverage: int):
    """Configure a grid trading bot."""
    session = get_session()
    try:
        # Verify client exists
        client = session.query(Client).filter(Client.client_id == client_id).first()
        if not client:
            raise click.ClickException(f"Client {client_id} not found")

        # Create or update bot configuration
        bot = session.query(Bot).filter(
            Bot.client_id == client_id,
            Bot.pair == pair
        ).first()

        if bot:
            bot.lower_price = lower
            bot.upper_price = upper
            bot.grids = grids
            bot.status = 'configured'
        else:
            bot = Bot(
                client_id=client_id,
                pair=pair,
                lower_price=lower,
                upper_price=upper,
                grids=grids,
                status='configured'
            )
            session.add(bot)

        session.commit()
        click.echo(f"Bot configured: client={client_id} pair={pair} status=configured")

    except Exception as e:
        logger.error(f"Failed to configure bot: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--pair', type=str, required=True, default='BTC/SOL', help='Trading pair')
@click.option('--capital', type=float, required=True, help='Capital in BTC')
def start_bot(client_id: int, pair: str, capital: float):
    """Start a configured grid trading bot."""
    session = get_session()
    try:
        bot = session.query(Bot).filter(
            Bot.client_id == client_id,
            Bot.pair == pair
        ).first()

        if not bot:
            raise click.ClickException(f"No configured bot found for client {client_id} and pair {pair}")

        if bot.status == 'active':
            raise click.ClickException(f"Bot is already active")

        bot.status = 'active'
        bot.capital_btc = capital
        session.commit()

        click.echo(f"Bot started: client={client_id} pair={pair} capital={capital}BTC")

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

        bot.status = 'stopped'
        session.commit()

        click.echo(f"Bot stopped: client={client_id} pair={pair}")

    except Exception as e:
        logger.error(f"Failed to stop bot: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close() 