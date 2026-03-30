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

async def account_worker(private_key: str, account_index: int):
    """
    Async worker function that runs the endless loop for a single account.
    """
    try:
        owner = load_keypair(private_key)
        owner_pubkey = owner.pubkey()
        destination = owner_pubkey
        
        # Update thread name for better logging visibility
        threading.current_thread().name = f"Wallet-{str(owner_pubkey)[:4]}"
        
        logger.info(f"START Monitoring | Wallet: {owner_pubkey}")
        
        async with AsyncClient(Config.RPC_URL) as client:
            cycle = 0
            while True:
                cycle += 1
                total_seen = 0
                total_closed = 0
                
                try:
                    for label, program_id in Config.TOKEN_PROGRAMS:
                        try:
                            items = get_token_accounts_raw(Config.RPC_URL, str(owner_pubkey), program_id)
                        except Exception as e:
                            logger.error(f"FETCH ERROR | {label} | {repr(e)}")
                            logger.debug(traceback.format_exc())
                            continue
                            
                        logger.info(f"Cycle #{cycle} | {label} | Found {len(items)} accounts")
                        
                        for item in items:
                            try:
                                token_account_str = item["pubkey"]
                                token_account = parse_pubkey(token_account_str)
                                amount, mint, state = extract_amount_and_info(item)
                                total_seen += 1
                                
                                logger.info(
                                    f"CHECK | {label} | Account: {token_account_str[:8]}... | "
                                    f"Mint: {mint[:8]}... | State: {state} | Amount: {amount}"
                                )
                                
                                if amount == 0:
                                    try:
                                        sig = await close_token_account_raw(
                                            client=client,
                                            payer=owner,
                                            token_account=token_account,
                                            destination=destination,
                                            token_program_id=program_id,
                                        )
                                        logger.info(f"CLOSED | {label} | {token_account_str} | Tx: {sig}")
                                        total_closed += 1
                                    except Exception as e:
                                        logger.error(f"CLOSE ERROR | {label} | {token_account_str} | {repr(e)}")
                                        logger.debug(traceback.format_exc())
                                        
                            except Exception as e:
                                logger.warning(f"SKIP | {label} | {item.get('pubkey')} | {repr(e)}")
                                
                    logger.info(f"Cycle #{cycle} Summary | Seen: {total_seen} | Closed: {total_closed}")
                    
                except Exception as e:
                    logger.error(f"Cycle #{cycle} encountered a critical error: {repr(e)}")
                    logger.debug(traceback.format_exc())
                    
                logger.info(f"Waiting {Config.CHECK_INTERVAL} seconds before next cycle...")
                await asyncio.sleep(Config.CHECK_INTERVAL)
                
    except Exception as e:
        logger.critical(f"Fatal error in worker thread: {e}")
        logger.debug(traceback.format_exc())

def run_worker_thread(private_key: str, account_index: int):
    """
    Wrapper to run the async worker inside a synchronous thread.
    """
    asyncio.run(account_worker(private_key, account_index))

def main():
    """
    Main entrypoint that initializes the bot and spawns threads for each account.
    """
    # Print custom banner
    print_banner(version="2.0.0-MultiThread")
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully.")
        
        private_keys = Config.get_private_keys()
        total_accounts = len(private_keys)
        
        logger.info(f"Found {total_accounts} account(s) in .env")
        logger.info(f"Check Interval: {Config.CHECK_INTERVAL} seconds")
        logger.info(f"Max Threads Allowed: {Config.MAX_THREADS}")
        
        threads = []
        for i, pk in enumerate(private_keys):
            if i >= Config.MAX_THREADS:
                logger.warning(f"Reached MAX_THREADS limit ({Config.MAX_THREADS}). Ignoring remaining accounts.")
                break
                
            t = threading.Thread(
                target=run_worker_thread, 
                args=(pk, i+1),
                daemon=True # Daemon threads exit when main thread exits
            )
            threads.append(t)
            t.start()
            # Slight delay between thread starts to avoid RPC rate limit spikes
            time.sleep(1)
            
        logger.info("All worker threads started. Bot is now running in endless loop. Press Ctrl+C to stop.")
        
        # Keep main thread alive to catch KeyboardInterrupt
        while True:
            time.sleep(1)
            
    except ValueError as ve:
        logger.critical(str(ve))
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user (KeyboardInterrupt). Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"Fatal error during bot initialization: {e}")
        logger.debug(traceback.format_exc())

if __name__ == "__main__":
    main()
