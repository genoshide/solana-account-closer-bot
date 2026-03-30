# Genoshide Token Account Closer Bot

A professional, modular Solana bot that automatically closes empty token accounts across multiple wallets, running in parallel threads with an endless loop.

---

## Features

- **Multi-Account via File** — Add as many wallets as needed in `private_key.txt`, one key per line.
- **Smart Destination Routing** — Rent SOL goes back to the wallet itself (single mode) or to a central `DESTINATION_WALLET` (multi mode).
- **Endless Loop** — Each wallet worker runs continuously without stopping.
- **Fully .env-Driven** — All settings (RPC, destination, delay, threads) controlled from `.env`.
- **Modular Architecture** — Clean `src/` package with single-responsibility modules.
- **Thread-Tagged Logging** — Every log line shows which wallet produced it.
- **Persistent File Log** — All output saved to `genoshide_bot.log`.
- **Supports SPL & Token-2022** — Scans and closes accounts from both token programs.

---

## Project Structure

```
genoshide_bot/
├── src/
│   ├── __init__.py       # Package marker
│   ├── config.py         # .env config, key loader, destination resolver
│   ├── logger.py         # Colored console + file logger
│   ├── banner.py         # ASCII banner display
│   ├── rpc.py            # Solana RPC HTTP communication
│   ├── wallet.py         # Keypair loading and Pubkey parsing
│   └── closer.py         # CloseAccount transaction logic
├── main.py               # Entrypoint and thread orchestration
├── private_key.txt       # Private keys (one base58 key per line)
├── .env.example          # Configuration template
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## Setup

**1. Install dependencies**
```bash
git clone https://github.com/genoshide/solana-account-closer-bot.git
cd solana-account-closer-bot
```

```bash
pip install -r requirements.txt
```

**2. Add your private keys to `private_key.txt`**

One base58 private key per line. Lines starting with `#` are comments and are ignored.

```
# private_key.txt
YOUR_BASE58_PRIVATE_KEY_1
YOUR_BASE58_PRIVATE_KEY_2
YOUR_BASE58_PRIVATE_KEY_3
```

**3. Configure `.env`**
```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `RPC_URL` | Always | Solana RPC endpoint |
| `DESTINATION_WALLET` | Multi-key only | Pubkey to receive all reclaimed rent SOL |
| `CHECK_INTERVAL` | Optional | Seconds between scan cycles (default: `5`) |
| `MAX_THREADS` | Optional | Max concurrent wallet threads (default: `10`) |

**4. Run the bot**
```bash
python main.py
```

---

## Destination Routing Logic

| Keys in `private_key.txt` | Rent SOL Destination |
|---|---|
| Exactly **1** key | Sent back to the wallet itself (`owner_pubkey`) |
| **2 or more** keys | Sent to `DESTINATION_WALLET` from `.env` |

---

## How It Works

1. Bot reads all private keys from `private_key.txt` on startup.
2. Each key gets its own dedicated thread (up to `MAX_THREADS`).
3. Every thread runs an **endless async loop** that:
   - Fetches all token accounts (SPL + Token-2022).
   - Checks each account for zero balance.
   - Sends a `CloseAccount` transaction for empty accounts, routing rent to the correct destination.
   - Waits `CHECK_INTERVAL` seconds, then repeats.
4. All activity is logged to console (colored, thread-tagged) and to `genoshide_bot.log`.

---

## Stopping the Bot

Press `Ctrl+C` at any time. All threads will shut down gracefully.

---

## Security

- **Never commit** `private_key.txt` or `.env` to version control.
- Add both to your `.gitignore`:
  ```
  private_key.txt
  .env
  ```
