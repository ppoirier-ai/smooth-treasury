import pytest
from click.testing import CliRunner
from cli.commands.bot_commands import configure_bot, start_bot, stop_bot
from cli.commands.client_commands import add_client_key
from common.database.models import Bot, Client, Trade

def test_complete_bot_flow(test_session):
    """Test complete bot flow from configuration to shutdown."""
    runner = CliRunner()
    
    # Add client
    result = runner.invoke(add_client_key, [
        '--client-id', '1',
        '--api-key', 'test_key',
        '--api-secret', 'test_secret'
    ])
    assert result.exit_code == 0
    client_id = 1
    
    # Configure bot
    result = runner.invoke(configure_bot, [
        '--client-id', str(client_id),
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '5'
    ])
    assert result.exit_code == 0
    
    # Start bot
    result = runner.invoke(start_bot, [
        '--client-id', str(client_id),
        '--pair', 'BTC/SOL',
        '--capital', '1.0'
    ])
    assert result.exit_code == 0
    
    # Verify bot status
    bot = test_session.query(Bot).filter_by(client_id=client_id).first()
    assert bot.status == 'active'
    
    # Stop bot
    result = runner.invoke(stop_bot, [
        '--client-id', str(client_id),
        '--pair', 'BTC/SOL'
    ])
    assert result.exit_code == 0
    
    # Verify bot stopped
    test_session.refresh(bot)
    assert bot.status == 'stopped' 