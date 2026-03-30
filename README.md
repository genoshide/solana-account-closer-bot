# Genoshide Token Account Closer Bot

A professional, modular Solana bot that automatically closes empty token accounts across multiple wallets, running in parallel threads with an endless loop.

---

## Features

- **Multi-Account Support** — Run as many wallets as needed, each in its own dedicated thread.
- **Endless Loop** — Each wallet worker runs continuously without stopping.
- **Fully .env-Driven** — All settings (RPC, keys, delay, threads) are controlled from a single `.env` file.
- **Modular Architecture** — Clean `src/` package with single-responsibility modules.
- **Professional Logging** — Colored console output with thread name tagging, plus persistent file logging to `genoshide_bot.log`.
- **Supports SPL & Token-2022** — Scans and closes accounts from both token programs.

---

## Project Structure

```
genoshide_bot/
├── src/
│   ├── __init__.py       # Package marker
│   ├── config.py         # Centralized .env configuration
│   ├── logger.py         # Colored console + file logger
│   ├── banner.py         # ASCII banner display
│   ├── rpc.py            # Solana RPC HTTP communication
│   ├── wallet.py         # Keypair loading and Pubkey parsing
│   └── closer.py         # CloseAccount transaction logic
├── main.py               # Entrypoint and thread orchestration
├── .env.example          # Configuration template
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure `.env`**
```bash
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description | Example |
|---|---|---|
| `RPC_URL` | Solana RPC endpoint URL | `https://api.mainnet-beta.solana.com` |
| `PRIVATE_KEYS` | Comma-separated base58 private keys | `KEY1,KEY2,KEY3` |
| `CHECK_INTERVAL` | Seconds between each scan cycle per wallet | `5` |
| `MAX_THREADS` | Max concurrent wallet worker threads | `10` |

**3. Run the bot**
```bash
python main.py
```

---

## How It Works

1. On startup, the bot reads all private keys from `PRIVATE_KEYS` in `.env`.
2. Each key is assigned to a dedicated thread (up to `MAX_THREADS`).
3. Every thread runs an **endless async loop** that:
   - Fetches all token accounts for that wallet (SPL + Token-2022).
   - Checks if each account has a zero balance.
   - Sends a `CloseAccount` transaction for every empty account, reclaiming rent SOL.
   - Waits `CHECK_INTERVAL` seconds, then repeats.
4. All activity is logged to the console (with colors) and to `genoshide_bot.log`.

---

## Stopping the Bot

Press `Ctrl+C` at any time. All threads will shut down gracefully.

---

## Log File

All logs are saved to `genoshide_bot.log` in the project root directory.
