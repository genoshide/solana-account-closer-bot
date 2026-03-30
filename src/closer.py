from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from .logger import logger
from .wallet import parse_pubkey

async def close_token_account_raw(
    client: AsyncClient, 
    payer: Keypair, 
    token_account: Pubkey, 
    destination: Pubkey, 
    token_program_id: str
) -> str:
    """
    Closes a token account by sending a CloseAccount instruction to the network.
    
    Args:
        client (AsyncClient): The Solana async RPC client.
        payer (Keypair): The payer and signer of the transaction.
        token_account (Pubkey): The token account to close.
        destination (Pubkey): The destination for the rent lamports.
        token_program_id (str): The token program ID.
        
    Returns:
        str: The transaction signature.
        
    Raises:
        Exception: If the transaction fails to send.
    """
    try:
        ix = Instruction(
            program_id=parse_pubkey(token_program_id),
            accounts=[
                AccountMeta(pubkey=token_account, is_signer=False, is_writable=True),
                AccountMeta(pubkey=destination, is_signer=False, is_writable=True),
                AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=False),
            ],
            data=bytes([9]), # CloseAccount instruction index
        )
        
        bh = await client.get_latest_blockhash()
        
        msg = Message.new_with_blockhash(
            [ix], 
            payer.pubkey(), 
            bh.value.blockhash
        )
        
        tx = Transaction.new_unsigned(msg)
        tx.sign([payer], bh.value.blockhash)
        
        sig = await client.send_transaction(tx)
        
        logger.debug(f"Successfully closed account {token_account}. Tx: {sig.value}")
        return str(sig.value)
        
    except Exception as e:
        logger.error(f"Failed to close token account {token_account}: {e}")
        raise
