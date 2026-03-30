import os
from dotenv import load_dotenv
from .logger import logger

# Load environment variables from .env file
load_dotenv()

# Path to the private key file (relative to project root)
PRIVATE_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "private_key.txt")


class Config:
    """Centralized configuration management for the Genoshide Bot."""

    # ------------------------------------------------------------------ #
    #  RPC Settings                                                        #
    # ------------------------------------------------------------------ #
    RPC_URL: str = os.getenv("RPC_URL", "")

    # ------------------------------------------------------------------ #
    #  Destination Wallet                                                  #
    #  Used only when more than one private key is loaded.                 #
    # ------------------------------------------------------------------ #
    DESTINATION_WALLET: str = os.getenv("DESTINATION_WALLET", "")

    # ------------------------------------------------------------------ #
    #  Loop & Threading Settings                                           #
    # ------------------------------------------------------------------ #
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "5"))
    MAX_THREADS: int = int(os.getenv("MAX_THREADS", "10"))

    # ------------------------------------------------------------------ #
    #  Solana Token Program Constants                                      #
    # ------------------------------------------------------------------ #
    SPL_TOKEN_PROGRAM_ID: str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    TOKEN_2022_PROGRAM_ID: str = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

    TOKEN_PROGRAMS = [
        ("SPL",        SPL_TOKEN_PROGRAM_ID),
        ("TOKEN_2022", TOKEN_2022_PROGRAM_ID),
    ]

    # ------------------------------------------------------------------ #
    #  Private Key Loader                                                  #
    # ------------------------------------------------------------------ #
    @classmethod
    def get_private_keys(cls) -> list[str]:
        """
        Reads private keys from ``private_key.txt``.

        Each non-empty, non-comment line is treated as one base58 private key.
        Lines starting with ``#`` are ignored.

        Returns:
            list[str]: Ordered list of base58 private key strings.

        Raises:
            FileNotFoundError: If ``private_key.txt`` does not exist.
        """
        if not os.path.isfile(PRIVATE_KEY_FILE):
            raise FileNotFoundError(
                f"private_key.txt not found at: {PRIVATE_KEY_FILE}\n"
                "Please create the file and add one base58 private key per line."
            )

        keys: list[str] = []
        with open(PRIVATE_KEY_FILE, "r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                keys.append(line)
                logger.debug(f"Loaded key #{len(keys)} from line {lineno} of private_key.txt")

        return keys

    # ------------------------------------------------------------------ #
    #  Destination Resolver                                                #
    # ------------------------------------------------------------------ #
    @classmethod
    def resolve_destination(cls, owner_pubkey_str: str, total_accounts: int) -> str:
        """
        Determines where rent SOL should be sent after closing a token account.

        Rules:
            - **Single account** (1 key in file) → send to ``owner_pubkey`` itself.
            - **Multi account**  (>1 keys in file) → send to ``DESTINATION_WALLET``
              from ``.env``.

        Args:
            owner_pubkey_str (str): The public key of the current wallet.
            total_accounts (int): Total number of private keys loaded.

        Returns:
            str: The destination public key string.

        Raises:
            ValueError: If multi-account mode is active but DESTINATION_WALLET
                        is not configured.
        """
        if total_accounts == 1:
            logger.debug("Single-account mode: destination = owner_pubkey")
            return owner_pubkey_str

        # Multi-account mode
        if not cls.DESTINATION_WALLET:
            raise ValueError(
                "Multi-account mode requires DESTINATION_WALLET to be set in .env, "
                "but it is currently empty."
            )
        logger.debug(
            f"Multi-account mode: destination = DESTINATION_WALLET "
            f"({cls.DESTINATION_WALLET[:8]}...)"
        )
        return cls.DESTINATION_WALLET

    # ------------------------------------------------------------------ #
    #  Startup Validation                                                  #
    # ------------------------------------------------------------------ #
    @classmethod
    def validate(cls) -> None:
        """
        Validates that all required configuration values are present and coherent.

        Raises:
            ValueError: On any missing or invalid configuration.
            FileNotFoundError: If ``private_key.txt`` is absent.
        """
        if not cls.RPC_URL:
            raise ValueError(
                "Configuration Error: RPC_URL is not set in the .env file."
            )

        keys = cls.get_private_keys()
        if not keys:
            raise ValueError(
                "Configuration Error: private_key.txt exists but contains no valid keys."
            )

        if len(keys) > 1 and not cls.DESTINATION_WALLET:
            raise ValueError(
                "Configuration Error: DESTINATION_WALLET must be set in .env "
                "when private_key.txt contains more than one key."
            )

        logger.info(f"Loaded {len(keys)} private key(s) from private_key.txt")
        if len(keys) > 1:
            logger.info(
                f"Multi-account mode active. "
                f"Rent destination: DESTINATION_WALLET = {cls.DESTINATION_WALLET[:8]}..."
            )
        else:
            logger.info("Single-account mode active. Rent destination: owner_pubkey")
