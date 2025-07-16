# XRPL Trust Line Removal Tool

A Python tool to remove trust lines with zero balance from XRP Ledger accounts. Each trust line reserves 0.2 XRP, and removing them releases this reserve back to your available balance.

## Problem

When you interact with tokens on the XRP Ledger, trust lines are created between your account and token issuers. Even after selling all tokens, these trust lines remain and each one locks 0.2 XRP as reserve. Over time, this can add up to hundreds of XRP locked in unused trust lines.

## Solution

This tool automatically removes all trust lines that have zero balance, releasing the reserved XRP back to your account.

## Requirements

- Python 3.7+
- xrpl-py library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Malomalsky/xrpl-trustline-remover.git
cd xrpl-trustline-remover
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup

You need your XRPL account seed (private key) to run this tool. Your seed is a string that starts with 's' (e.g., `sEdV...`).

**Where to find your seed:**
- Most XRPL wallets have an "Export" or "Backup" option
- XUMM: Settings → Account → Export account
- Toast Wallet: Settings → Backup
- Ledger hardware wallet: Use recovery phrase with wallet software

## Usage

### Method 1: Environment Variable (Recommended)

Set your seed as an environment variable:

```bash
export XRPL_SEED="sEdVYourActualSeedHere"
python remove_trustlines.py
```

### Method 2: Interactive Input

Run the script and enter your seed when prompted:

```bash
python remove_trustlines.py
```

The tool will ask for your seed securely (characters won't be displayed on screen).

### Method 3: Command Line (Not Recommended)

Only for testing. Your seed will be visible in command history:

```bash
XRPL_SEED="sEdVYourActualSeedHere" python remove_trustlines.py
```

## How It Works

1. Connects to XRP Ledger mainnet
2. Fetches all trust lines with zero balance
3. Sends TrustSet transactions with appropriate flags to remove them
4. Reports progress and final results

## Important Notes

- Only removes trust lines with **zero balance**
- Each removed trust line releases 0.2 XRP from reserve
- The process may take time if you have many trust lines
- Some trust lines may fail to remove if the issuer account no longer exists

## Security

- Your seed is never stored or transmitted anywhere except to sign transactions
- All operations happen directly between your machine and the XRP Ledger
- Consider using a read-only environment when entering sensitive information

**Important Security Notes:**
- Never share your seed with anyone
- Keep your seed safe and backed up
- Consider testing on a small account first
- This tool only works with mainnet (real XRP)

## Transaction Fees

Each trust line removal costs a small network fee (typically 0.000012 XRP). If you have 1000 trust lines to remove, expect to pay about 0.012 XRP in fees total.

## Example Output

```
XRPL Trust Line Removal Tool
==================================================
Wallet address: rYourXRPAddressHere
--------------------------------------------------
Initial OwnerCount: 1250
Balance: 300.5 XRP

Fetching trust lines...
Found 1200 trust lines with zero balance

Removing 1200 trust lines...
--------------------------------------------------

Progress: 10.0% (120/1200)
Current OwnerCount: 1130

...

==================================================
RESULTS:
Successfully removed: 1150
Already removed: 45
Failed: 5

OwnerCount: 1250 -> 95
Released reserve: 231.0 XRP
```

## License

MIT