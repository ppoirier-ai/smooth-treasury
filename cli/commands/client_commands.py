import click
from cryptography.fernet import Fernet
import os
from common.database.connection import get_session
from common.database.models import Client
from common.utils.logger import setup_logger
from common.utils.config import get_config

logger = setup_logger(__name__)

def get_encryption_key() -> bytes:
    """Get encryption key from environment or config."""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        config = get_config()
        key = config.get('encryption_key')
    if not key:
        raise ValueError("Encryption key not found in environment or config")
    return key.encode()

def encrypt_key(key: str) -> str:
    """Encrypt API key using Fernet."""
    cipher_key = get_encryption_key()
    f = Fernet(cipher_key)
    return f.encrypt(key.encode()).decode()

@click.command()
@click.option('--client-id', type=int, required=True, help='Client ID')
@click.option('--api-key', type=str, required=True, help='Exchange API key')
@click.option('--api-secret', type=str, required=True, help='Exchange API secret')
def add_client_key(client_id: int, api_key: str, api_secret: str):
    """Add a new client with API keys."""
    session = get_session()
    try:
        # Check if client already exists
        existing = session.query(Client).filter_by(client_id=client_id).first()
        if existing:
            raise click.ClickException(f"Client {client_id} already exists")

        # Create new client
        client = Client(
            client_id=client_id,
            api_key=api_key,
            api_secret=api_secret
        )
        session.add(client)
        session.commit()
        click.echo(f"Added client {client_id}")

    except Exception as e:
        logger.error(f"Failed to add client: {str(e)}")
        raise click.ClickException(str(e))
    finally:
        session.close() 