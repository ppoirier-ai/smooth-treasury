import click
from cli.commands import bot_commands, client_commands, metrics_commands

@click.group()
def cli():
    """Grid Trading Bot CLI"""
    pass

# Register command groups
cli.add_command(bot_commands.configure_bot)
cli.add_command(bot_commands.start_bot)
cli.add_command(bot_commands.stop_bot)
cli.add_command(client_commands.add_client_key)
cli.add_command(metrics_commands.status)
cli.add_command(metrics_commands.metrics)

if __name__ == "__main__":
    cli() 