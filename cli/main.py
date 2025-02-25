import click
from cli.commands.bot_commands import configure_bot, start_bot, stop_bot
from cli.commands.client_commands import add_client_key
from cli.commands.metrics_commands import status, metrics

@click.group()
def cli():
    """Grid Trading Bot CLI"""
    pass

# Register commands
cli.add_command(configure_bot)
cli.add_command(start_bot)
cli.add_command(stop_bot)
cli.add_command(add_client_key)
cli.add_command(status)
cli.add_command(metrics)

if __name__ == "__main__":
    cli() 