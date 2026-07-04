"""Day 1 — TON testnet chain reader.

Reads live chain state via the TonCenter v3 REST API (an indexer over a
real TON node). Three questions, three functions:
  1. Where is the chain right now?          -> get_latest_block()
  2. What is the state of one account?      -> get_address_info()
  3. What happened to that account lately?  -> get_transactions()
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables (the proper grep/cut)

BASE = "https://testnet.toncenter.com/api/v3"
HEADERS = {"X-API-Key": os.getenv("TONCENTER_API_KEY", "")}
MY_WALLET = "0QDJqqf9LXrJcywKC7jgHT68ZUSq_gJfHCPii3qg7yPEQ8Is"

NANO = 1_000_000_000  # 1 TON = 10^9 nanotons; all on-chain amounts are ints of these


def api_get(path: str, params: dict | None = None) -> dict:
    """Send one GET request to TonCenter and return the parsed JSON.

    Shared plumbing for every function below:
      - builds the URL from BASE + endpoint path
      - attaches query params (address, limit, ...) if given
      - sends the API key in the X-API-Key header (auth without leaking
        the key into URLs/logs)
      - timeout=10 so a dead network fails fast instead of hanging
      - raise_for_status() turns any 4xx/5xx into a loud Python exception
        (the -sS of the requests world)
    """
    resp = requests.get(f"{BASE}/{path}", params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ---------- 1. COMPLETE ----------
def get_latest_block() -> dict:
    """Return the newest masterchain block: {seqno, time, root_hash}.

    Endpoint: GET /masterchainInfo — the same call as the week's curl.
    The response's "last" object is the coordinator chain's newest block;
    we keep its position (seqno), wall-clock time (gen_utime) and content
    fingerprint (root_hash) and drop the consensus plumbing.
    A rising seqno across runs = proof we're reading a live chain.
    """
    data = api_get("masterchainInfo")
    last = data["last"]
    return {
        "seqno": last["seqno"],
        "time": last["gen_utime"],
        "root_hash": last["root_hash"],
    }


# ---------- 2. YOURS ----------
def get_address_info(addr: str) -> dict:
    """Return one account's current state: {balance_ton, status, last_tx_lt}.

    Endpoint: GET /accountStates?address=...
    TON is an account-based chain: every address has a live state record
    (balance in nanotons, status, code/data if it's a contract). This asks
    the indexer for that record — pointed at MY_WALLET, the faucet TON
    from Day 0 should appear here.

    Fields to extract (see TODO):
      balance      -> arrives as a STRING of nanotons; int() it, / NANO
      status       -> "active" = deployed & running; "uninit" = the address
                      has funds but no code deployed yet (wallets start so)
      last_transaction_lt -> logical time of the account's newest tx; this
                      lt is also the pagination cursor for function 3
    """
    data = api_get("accountStates", {"address": addr, "include_boc": "false"})
    account = data["accounts"][0]
    # TODO(you): return {"balance_ton": ..., "status": ..., "last_tx_lt": ...}
    
    return {
        "balance": int(account["balance"]) / NANO,
        "status": account["status"],
        "last_transaction_lt": account["last_transaction_lt"],
    }


# ---------- 3. YOURS ----------
def get_transactions(addr: str, limit: int = 5) -> list[dict]:
    """Return the account's recent transactions, newest first.

    Endpoint: GET /transactions?account=...&limit=...
    Remember the TON definition: a transaction = one account processing ONE
    incoming message (message in -> state change -> messages out). So the
    faucet top-up shows up here as a tx whose in_msg came FROM the faucet's
    address, carrying the value. Results are ordered by lt — the causal
    clock doing its practical job.

    Per tx, extract (see TODO):
      lt         -> the transaction's position on the causal clock
      from       -> in_msg["source"]; None for some txs (think about which)
      value_ton  -> in_msg["value"], string nanotons -> TON
      comment    -> optional text riding in the message body; it's nested
                    inside in_msg["message_content"] — print and explore.
                    v3 pre-decodes it; tomorrow you decode it yourself.
    """
    data = api_get("transactions", {"account": addr, "limit": limit})
    txs = data["transactions"]
    results = []
    for tx in txs:
        in_msg = tx.get("in_msg") or {}
        results.append({
            # TODO(you): "lt", "from", "value_ton", "comment"
            "lt": tx["lt"],
            "from": in_msg["source"],
            "value_ton": int(in_msg["value"]) / NANO, 
            "comment": in_msg["message_content"]["decoded"]["comment"],
            "aborted": (tx.get("description") or {}).get("aborted", False),
            "credited": bool(in_msg.get("value")) and not any(
                m.get("bounced") for m in (tx.get("out_msgs") or [])
            ),
        })
    return results


if __name__ == "__main__":
    print("latest block:", get_latest_block())
    print("my wallet:   ", get_address_info(MY_WALLET))
    get_transactions(MY_WALLET, 5)
    for t in get_transactions(MY_WALLET, 5):
         print("tx:", t)