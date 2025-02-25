import click
from cryptography.fernet import Fernet
from common.database.connection import get_session
from common.database.models import Client
from common.utils.logger import setup_logger
from common.utils.config import get_config

logger = setup_logger(__name__)

def encrypt_key(key: str) -> str:
    """Encrypt API key using Fernet."""
    config = get_config()
    cipher_key = config.get('encryption_key', Fernet.generate_key())
    f = Fernet(cipher_key)
    return f.encrypt(key.encode()).decode()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--key', type=str, required=True, help='Binance API key')
@click.option('--secret', type=str, required=True, help='Binance API secret')
def add_client_key(client_id: int, key: str, secret: str):
    """Add or update a client's Binance API keys."""
    session = get_session()
    try:
        # Encrypt keys before storing
        encrypted_key = encrypt_key(key)
        encrypted_secret = encrypt_key(secret)

        # Create or update client
        client = session.query(Client).filter(Client.client_id == client_id).first()
        if client:
            client.api_key = encrypted_key
            client.api_secret = encrypted_secret
        else:
            client = Client(
                client_id=client_id,
                api_key=encrypted_key,
                api_secret=encrypted_secret
            )
            session.add(client)

        session.commit()
        click.echo(f"Client API keys stored: client={client_id}")

    except Exception as e:
        logger.error(f"Failed to store client API keys: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close() 