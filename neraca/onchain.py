"""MAKELAR's on-chain arm (Base).

- stake_guarantee(): puts real USDC behind an APPROVE_WITH_GUARANTEE verdict
  (CDP server wallet, Base Sepolia) and journals the stake into COLD memory —
  the bureau remembers the skin it put in the game.
- b20_read(): free eth_call against Coinbase Tokenized Stocks (B20 standard)
  on Base mainnet; no wallet, no gas.

CLI:  python -m neraca.onchain wallet|b20|stake <counterparty> <usdc>
Env:  CDP_API_KEY_ID, CDP_API_KEY_SECRET, CDP_WALLET_SECRET (portal.cdp.coinbase.com)
"""

import asyncio
import json
import os
import sys

import httpx

USDC_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
AAPLC_B20 = "0xb200000000000000000000C2e324d24d7eEcd1fb"  # Coinbase Tokenized Stock AAPL
BASE_MAINNET_RPC = "https://mainnet.base.org"
BASESCAN = "https://sepolia.basescan.org/tx/"


def _require_creds() -> None:
    missing = [k for k in ("CDP_API_KEY_ID", "CDP_API_KEY_SECRET", "CDP_WALLET_SECRET")
               if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"CDP credentials missing: {', '.join(missing)} "
                         "(create them at portal.cdp.coinbase.com, put them in .env)")


def _erc20_transfer_data(to: str, amount_base_units: int) -> str:
    return ("0xa9059cbb"
            + to.lower().removeprefix("0x").rjust(64, "0")
            + hex(amount_base_units)[2:].rjust(64, "0"))


async def wallet() -> dict:
    """Create/show MAKELAR's CDP server wallet and vault, faucet both."""
    _require_creds()
    from cdp import CdpClient
    async with CdpClient() as cdp:
        makelar = await cdp.evm.get_or_create_account(name="neraca-makelar")
        vault = await cdp.evm.get_or_create_account(name="neraca-vault")
        for acct in (makelar, vault):
            for token in ("eth", "usdc"):
                try:
                    await cdp.evm.request_faucet(address=acct.address,
                                                 network="base-sepolia", token=token)
                except Exception as e:  # faucet rate limits are fine; balances may already exist
                    print(f"faucet {token} for {acct.address}: {e}", file=sys.stderr)
        return {"makelar": makelar.address, "vault": vault.address}


async def stake_guarantee(counterparty: str, amount_usdc: float) -> dict:
    """Send the guarantee stake (USDC, Base Sepolia) and journal it."""
    _require_creds()
    from cdp import CdpClient
    from cdp.evm_transaction_types import TransactionRequestEIP1559

    from .memory import client
    m = client()
    state = m.get_state(f"negotiation:{counterparty}")
    verdict = (state or {}).get("body", {}).get("verdict")
    if verdict != "APPROVE_WITH_GUARANTEE":
        raise SystemExit(f"no open APPROVE_WITH_GUARANTEE negotiation for {counterparty} "
                         f"(found: {verdict}) - the stake is priced by memory, not typed by hand")

    amount = int(amount_usdc * 1_000_000)
    async with CdpClient() as cdp:
        makelar = await cdp.evm.get_or_create_account(name="neraca-makelar")
        vault = await cdp.evm.get_or_create_account(name="neraca-vault")
        tx = await cdp.evm.send_transaction(
            address=makelar.address,
            transaction=TransactionRequestEIP1559(
                to=USDC_SEPOLIA, data=_erc20_transfer_data(vault.address, amount)),
            network="base-sepolia",
        )
    tx_hash = getattr(tx, "transaction_hash", tx)
    m.write_event(acted=[f"staked {amount_usdc} USDC guarantee on {counterparty}"],
                  extra={"kind": "guarantee_stake", "counterparty": counterparty,
                         "amount_usdc": amount_usdc, "tx": str(tx_hash)})
    return {"tx": str(tx_hash), "explorer": BASESCAN + str(tx_hash),
            "from": makelar.address, "vault": vault.address, "amount_usdc": amount_usdc}


def b20_read() -> dict:
    """Free read of a live B20 tokenized stock on Base mainnet (no wallet/gas)."""
    def call(sig: str) -> str:
        r = httpx.post(BASE_MAINNET_RPC, json={
            "jsonrpc": "2.0", "id": 1, "method": "eth_call",
            "params": [{"to": AAPLC_B20, "data": sig}, "latest"]}, timeout=15)
        r.raise_for_status()
        return r.json()["result"]

    def decode_str(hexdata: str) -> str:
        raw = bytes.fromhex(hexdata.removeprefix("0x"))
        strlen = int.from_bytes(raw[32:64], "big")
        return raw[64:64 + strlen].decode()

    return {
        "contract": AAPLC_B20,
        "standard": "B20 (Base native token standard, Beryl hardfork)",
        "name": decode_str(call("0x06fdde03")),
        "symbol": decode_str(call("0x95d89b41")),
        "totalSupply": int(call("0x18160ddd"), 16),
    }


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "b20"
    if cmd == "b20":
        print(json.dumps(b20_read(), indent=2))
    elif cmd == "wallet":
        print(json.dumps(asyncio.run(wallet()), indent=2))
    elif cmd == "stake":
        print(json.dumps(asyncio.run(stake_guarantee(sys.argv[2], float(sys.argv[3]))), indent=2))
    else:
        raise SystemExit("usage: python -m neraca.onchain [b20|wallet|stake <counterparty> <usdc>]")


if __name__ == "__main__":
    main()
