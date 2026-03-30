import requests
from typing import List, Dict, Any, Tuple
from .logger import logger

def get_token_accounts_raw(rpc_url: str, owner_pubkey: str, program_id: str) -> List[Dict[str, Any]]:
    """
    Fetches raw token accounts for a given owner and program ID.
    
    Args:
        rpc_url (str): The Solana RPC URL.
        owner_pubkey (str): The public key of the owner.
        program_id (str): The token program ID (SPL or Token2022).
        
    Returns:
        List[Dict[str, Any]]: A list of token account dictionaries.
        
    Raises:
        RuntimeError: If the RPC call fails or returns an error.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            str(owner_pubkey),
            {"programId": program_id},
            {"encoding": "jsonParsed"}
        ]
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            error_msg = data["error"]
            logger.error(f"RPC Error fetching accounts for {owner_pubkey[:8]}... : {error_msg}")
            raise RuntimeError(error_msg)
            
        return data.get("result", {}).get("value", [])
        
    except requests.RequestException as e:
        logger.error(f"HTTP Request failed during getTokenAccountsByOwner for {owner_pubkey[:8]}... : {e}")
        raise

def extract_amount_and_info(item: Dict[str, Any]) -> Tuple[int, str, str]:
    """
    Extracts the token amount, mint address, and account state from the raw RPC response.
    
    Args:
        item (Dict[str, Any]): The raw token account dictionary.
        
    Returns:
        Tuple[int, str, str]: A tuple containing (amount, mint, state).
    """
    try:
        parsed = item["account"]["data"]["parsed"]
        info = parsed["info"]
        amount = int(info.get("tokenAmount", {}).get("amount", "0"))
        mint = info.get("mint", "unknown")
        state = info.get("state", "unknown")
        return amount, mint, state
    except KeyError as e:
        logger.error(f"Failed to parse token account info. Missing key: {e}")
        return 0, "unknown", "unknown"
