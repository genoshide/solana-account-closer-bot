import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration management for the Genoshide Bot."""
    
    # RPC Settings
    RPC_URL = os.getenv("RPC_URL", "")
    
    # Account Settings (Comma-separated base58 private keys)
    PRIVATE_KEYS_BASE58 = os.getenv("PRIVATE_KEYS", "")
    
    # Threading & Loop Settings
    MAX_THREADS = int(os.getenv("MAX_THREADS", "5"))
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "5"))
    
    # Constants
    SPL_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
    
    TOKEN_PROGRAMS = [
        ("SPL", SPL_TOKEN_PROGRAM_ID),
        ("TOKEN_2022", TOKEN_2022_PROGRAM_ID),
    ]

    @classmethod
    def get_private_keys(cls):
        """Returns a list of private keys parsed from the environment variable."""
        if not cls.PRIVATE_KEYS_BASE58:
            return []
        return [key.strip() for key in cls.PRIVATE_KEYS_BASE58.split(",") if key.strip()]

    @classmethod
    def validate(cls):
        """Validates that all required configuration variables are set."""
        if not cls.RPC_URL:
            raise ValueError("Configuration Error: RPC_URL is not set in the .env file.")
        if not cls.get_private_keys():
            raise ValueError("Configuration Error: PRIVATE_KEYS is not set or empty in the .env file.")
