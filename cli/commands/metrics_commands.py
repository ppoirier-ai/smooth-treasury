import click
from common.database.connection import get_session
from common.database.models import Bot, Trade
from common.utils.logger import setup_logger
from sqlalchemy import func
from datetime import datetime, timedelta

logger = setup_logger(__name__)

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
def status(client_id: int):
    """Check the status of all bots for a client."""
    session = get_session()
    try:
        bots = session.query(Bot).filter(Bot.client_id == client_id).all()
        
        if not bots:
            click.echo(f"No bots found for client={client_id}")
            return

        for bot in bots:
            click.echo(
                f"client={client_id} "
                f"pair={bot.pair} "
                f"status={bot.status} "
                f"capital={bot.capital_btc}BTC"
            )

    except Exception as e:
        logger.error(f"Failed to get bot status: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
def metrics(client_id: int):
    """Get performance metrics for a client's bots."""
    session = get_session()
    try:
        # Calculate 24h metrics
        yesterday = datetime.now() - timedelta(days=1)
        
        # Get total BTC accumulated and 24h profit
        daily_metrics = session.query(
            func.sum(Trade.profit_btc).label('profit_24h')
        ).join(Bot).filter(
            Bot.client_id == client_id,
            Trade.timestamp >= yesterday
        ).first()

        total_metrics = session.query(
            func.sum(Trade.profit_btc).label('total_profit')
        ).join(Bot).filter(
            Bot.client_id == client_id
        ).first()

        # Get active capital
        active_capital = session.query(
            func.sum(Bot.capital_btc)
        ).filter(
            Bot.client_id == client_id,
            Bot.status == 'active'
        ).scalar() or 0

        profit_24h = daily_metrics.profit_24h or 0
        total_profit = total_metrics.total_profit or 0
        
        # Calculate ROI
        roi_24h = (profit_24h / active_capital * 100) if active_capital > 0 else 0
        roi_total = (total_profit / active_capital * 100) if active_capital > 0 else 0

        click.echo(
            f"client={client_id} "
            f"btc_profit_24h={profit_24h:.8f} "
            f"btc_profit_total={total_profit:.8f} "
            f"roi_24h={roi_24h:.2f}% "
            f"roi_total={roi_total:.2f}% "
            f"active_capital={active_capital}BTC"
        )

    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close() 