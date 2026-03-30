from solders.pubkey import Pubkey
from solders.keypair import Keypair
from typing import Union
from .logger import logger

def parse_pubkey(x: Union[str, Pubkey]) -> Pubkey:
    """
    Parses a string into a Pubkey object, or returns the object if it's already a Pubkey.
    
    Args:
        x (Union[str, Pubkey]): The string or Pubkey to parse.
        
    Returns:
        Pubkey: The parsed Pubkey object.
    """
    try:
        return Pubkey.from_string(x) if not isinstance(x, Pubkey) else x
    except ValueError as e:
        logger.error(f"Invalid Pubkey string: {x}")
        raise ValueError(f"Failed to parse pubkey: {e}")

def load_keypair(private_key_base58: str) -> Keypair:
    """
    Loads a Solana Keypair from a base58 encoded private key string.
    
    Args:
        private_key_base58 (str): The base58 encoded private key.
        
    Returns:
        Keypair: The loaded Keypair object.
    """
    try:
        return Keypair.from_base58_string(private_key_base58)
    except Exception as e:
        logger.error("Failed to load Keypair from base58 string. Ensure the key in .env is correct.")
        raise RuntimeError(f"Keypair loading failed: {e}")
