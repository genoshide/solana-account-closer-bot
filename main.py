import asyncio
import threading
import traceback
import time
from solana.rpc.async_api import AsyncClient
from src.logger import logger
from src.config import Config
from src.banner import print_banner
from src.rpc import get_token_accounts_raw, extract_amount_and_info
from src.wallet import load_keypair, parse_pubkey
from src.closer import close_token_account_raw


async def account_worker(private_key: str, account_index: int, total_accounts: int) -> None:
    """
    Async worker that runs an endless scan-and-close loop for a single wallet.

    Destination routing:
        - ``total_accounts == 1``  → rent SOL sent back to the wallet itself.
        - ``total_accounts  > 1``  → rent SOL forwarded to ``DESTINATION_WALLET``.

    Args:
        private_key (str): Base58-encoded private key for this wallet.
        account_index (int): 1-based index used for display/logging.
        total_accounts (int): Total number of wallets loaded from private_key.txt.
    """
    try:
        owner = load_keypair(private_key)
        owner_pubkey = owner.pubkey()
        owner_pubkey_str = str(owner_pubkey)

        # Tag the thread name with a short wallet prefix for easy log filtering
        threading.current_thread().name = f"Wallet-{owner_pubkey_str[:6]}"

        # Resolve destination once per worker (never changes during runtime)
        destination_str = Config.resolve_destination(owner_pubkey_str, total_accounts)
        destination = parse_pubkey(destination_str)

        # Log startup info for this worker
        logger.info(
            f"[{account_index}/{total_accounts}] Worker started | "
            f"Wallet: {owner_pubkey_str}"
        )
        logger.info(
            f"[{account_index}/{total_accounts}] Rent destination: "
            f"{'self (owner)' if destination_str == owner_pubkey_str else destination_str}"
        )

        async with AsyncClient(Config.RPC_URL) as client:
            cycle = 0
            while True:
                cycle += 1
                total_seen = 0
                total_closed = 0
                total_skipped = 0

                try:
                    for label, program_id in Config.TOKEN_PROGRAMS:
                        # ── Fetch token accounts ────────────────────────────
                        try:
                            items = get_token_accounts_raw(
                                Config.RPC_URL, owner_pubkey_str, program_id
                            )
                        except Exception as e:
                            logger.error(
                                f"FETCH ERROR | {label} | Wallet: {owner_pubkey_str[:8]}... | "
                                f"{repr(e)}"
                            )
                            logger.debug(traceback.format_exc())
                            continue

                        logger.info(
                            f"Cycle #{cycle} | {label} | "
                            f"Wallet: {owner_pubkey_str[:8]}... | "
                            f"Found {len(items)} account(s)"
                        )

                        # ── Process each token account ──────────────────────
                        for item in items:
                            try:
                                token_account_str = item["pubkey"]
                                token_account = parse_pubkey(token_account_str)
                                amount, mint, state = extract_amount_and_info(item)
                                total_seen += 1

                                logger.info(
                                    f"CHECK | {label} | "
                                    f"Account: {token_account_str[:8]}... | "
                                    f"Mint: {mint[:8]}... | "
                                    f"State: {state} | "
                                    f"Amount: {amount}"
                                )

                                # ── Close if balance is zero ────────────────
                                if amount == 0:
                                    try:
                                        sig = await close_token_account_raw(
                                            client=client,
                                            payer=owner,
                                            token_account=token_account,
                                            destination=destination,
                                            token_program_id=program_id,
                                        )
                                        logger.info(
                                            f"CLOSED | {label} | "
                                            f"{token_account_str} | "
                                            f"Rent → {destination_str[:8]}... | "
                                            f"Tx: {sig}"
                                        )
                                        total_closed += 1
                                    except Exception as e:
                                        logger.error(
                                            f"CLOSE ERROR | {label} | "
                                            f"{token_account_str} | {repr(e)}"
                                        )
                                        logger.debug(traceback.format_exc())
                                else:
                                    total_skipped += 1

                            except Exception as e:
                                logger.warning(
                                    f"SKIP | {label} | "
                                    f"{item.get('pubkey', 'unknown')} | {repr(e)}"
                                )

                    # ── Cycle summary ───────────────────────────────────────
                    logger.info(
                        f"Cycle #{cycle} Summary | "
                        f"Wallet: {owner_pubkey_str[:8]}... | "
                        f"Seen: {total_seen} | "
                        f"Closed: {total_closed} | "
                        f"Skipped (non-zero): {total_skipped}"
                    )

                except Exception as e:
                    logger.error(
                        f"Cycle #{cycle} critical error | "
                        f"Wallet: {owner_pubkey_str[:8]}... | {repr(e)}"
                    )
                    logger.debug(traceback.format_exc())

                logger.info(
                    f"Sleeping {Config.CHECK_INTERVAL}s before next cycle | "
                    f"Wallet: {owner_pubkey_str[:8]}..."
                )
                await asyncio.sleep(Config.CHECK_INTERVAL)

    except Exception as e:
        logger.critical(f"Fatal error in worker thread: {e}")
        logger.debug(traceback.format_exc())


def run_worker_thread(private_key: str, account_index: int, total_accounts: int) -> None:
    """
    Synchronous wrapper that runs the async ``account_worker`` inside a thread.

    Args:
        private_key (str): Base58-encoded private key.
        account_index (int): 1-based index for display.
        total_accounts (int): Total wallets loaded.
    """
    asyncio.run(account_worker(private_key, account_index, total_accounts))


def main() -> None:
    """
    Bot entrypoint.

    1. Prints the Genoshide banner.
    2. Validates configuration and loads private keys from ``private_key.txt``.
    3. Spawns one daemon thread per wallet (up to ``MAX_THREADS``).
    4. Keeps the main thread alive until ``Ctrl+C``.
    """
    print_banner(version="2.1.0-MultiAccount")

    try:
        # ── Validate config and load keys ───────────────────────────────────
        Config.validate()
        logger.info("Configuration validated successfully.")

        private_keys = Config.get_private_keys()
        total_accounts = len(private_keys)

        logger.info(f"Total accounts loaded  : {total_accounts}")
        logger.info(f"Check interval         : {Config.CHECK_INTERVAL} second(s)")
        logger.info(f"Max concurrent threads : {Config.MAX_THREADS}")

        if total_accounts > Config.MAX_THREADS:
            logger.warning(
                f"Accounts ({total_accounts}) exceed MAX_THREADS ({Config.MAX_THREADS}). "
                f"Only the first {Config.MAX_THREADS} account(s) will be processed."
            )

        # ── Spawn worker threads ────────────────────────────────────────────
        threads: list[threading.Thread] = []
        for i, pk in enumerate(private_keys[:Config.MAX_THREADS]):
            t = threading.Thread(
                target=run_worker_thread,
                args=(pk, i + 1, total_accounts),
                daemon=True,  # Exit automatically when main thread exits
            )
            threads.append(t)
            t.start()
            logger.info(f"Thread {i + 1}/{min(total_accounts, Config.MAX_THREADS)} started.")
            # Stagger thread starts to avoid simultaneous RPC bursts
            time.sleep(0.5)

        logger.info(
            "All worker threads are running. "
            "Bot is in endless loop mode. Press Ctrl+C to stop."
        )

        # ── Keep main thread alive ──────────────────────────────────────────
        while True:
            time.sleep(1)

    except (ValueError, FileNotFoundError) as e:
        logger.critical(str(e))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt). Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"Unexpected fatal error during initialization: {e}")
        logger.debug(traceback.format_exc())


if __name__ == "__main__":
    main()
