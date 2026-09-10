"""MAKELAR's on-chain arm (Base).

- stake_guarantee(): puts real USDC behind an APPROVE_WITH_GUARANTEE verdict
  (CDP server wallet, Base Sepolia) and journals the stake into COLD memory —
  the bureau remembers the skin it put in the game.
- b20_read(): free eth_call against Coinbase Tokenized Stocks (B20 standard)
  on Base mainnet; no wallet, no gas.

Two ways to hold the wallet, pick either:
  - NERACA_STAKE_KEY: any Base Sepolia private key. No account, no portal.
  - CDP_API_KEY_ID / _SECRET / CDP_WALLET_SECRET: CDP server wallets.
The key path wins when both are set. The stake itself is identical either way -
a real USDC transfer() on Base Sepolia, gated by memory before either fires.

CLI:  python -m neraca.onchain wallet|b20|stake <counterparty> <usdc>
"""

import asyncio
import json
import os
import sys

import httpx

USDC_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
AAPLC_B20 = "0xb200000000000000000000C2e324d24d7eEcd1fb"  # Coinbase Tokenized Stock AAPL
BASE_MAINNET_RPC = "https://mainnet.base.org"
BASE_SEPOLIA_RPC = "https://sepolia.base.org"
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


def local_wallet() -> dict:
    """No-portal path: mint (or report) the staking wallet and its vault.

    Prints what to paste into .env and what to point a faucet at. Run it again
    after fauceting - it reports balances, so you can see the funds land.
    """
    from eth_account import Account
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC))

    def balances(addr: str) -> dict:
        usdc = w3.eth.call({"to": Web3.to_checksum_address(USDC_SEPOLIA),
                            "data": "0x70a08231" + addr.lower().removeprefix("0x").rjust(64, "0")})
        return {"eth": w3.from_wei(w3.eth.get_balance(Web3.to_checksum_address(addr)), "ether"),
                "usdc": int(usdc.hex() or "0", 16) / 1_000_000}

    key = os.environ.get("NERACA_STAKE_KEY")
    if not key:
        stake, vault = Account.create(), Account.create()
        print("Two fresh Base Sepolia wallets. Paste these into .env:\n")
        print(f"NERACA_STAKE_KEY={stake.key.hex()}")
        print(f"NERACA_VAULT={vault.address}")
        print(f"NERACA_BUYER_KEY={vault.key.hex()}   # doubles as the x402 buyer\n")
        print(f"Then faucet the staking wallet with Base Sepolia ETH and USDC:\n"
              f"  {stake.address}\n"
              f"  ETH:  https://www.alchemy.com/faucets/base-sepolia\n"
              f"  USDC: https://faucet.circle.com  (pick Base Sepolia)\n"
              f"Re-run this command to watch the balances land.")
        return {"staking_wallet": stake.address, "vault": vault.address, "funded": False}

    acct = Account.from_key(key)
    vault = os.environ.get("NERACA_VAULT") or os.environ.get("NERACA_PAY_TO")
    return {"staking_wallet": acct.address, "balances": balances(acct.address),
            "vault": vault, "vault_balances": balances(vault) if vault else None}


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
    # memory gate first, on purpose: the refusal is demonstrable with no keys at all
    from .memory import client
    m = client()
    state = m.get_state(f"negotiation:{counterparty}")
    verdict = (state or {}).get("body", {}).get("verdict")
    if verdict != "APPROVE_WITH_GUARANTEE":
        raise SystemExit(f"no open APPROVE_WITH_GUARANTEE negotiation for {counterparty} "
                         f"(found: {verdict}) - the stake is priced by memory, not typed by hand")

    amount = int(amount_usdc * 1_000_000)
    if os.environ.get("NERACA_STAKE_KEY"):
        return _stake_with_key(counterparty, amount_usdc, amount, m)

    _require_creds()
    from cdp import CdpClient
    from cdp.evm_transaction_types import TransactionRequestEIP1559

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


def _vault_address(sender: str) -> str:
    vault = os.environ.get("NERACA_VAULT") or os.environ.get("NERACA_PAY_TO")
    if not vault:
        raise SystemExit(
            "set NERACA_VAULT to the address the guarantee is escrowed to - any "
            "second address you control (`python -m neraca.onchain wallet` mints one)")
    if vault.lower() == sender.lower():
        raise SystemExit("NERACA_VAULT must differ from the staking wallet")
    return vault


def _stake_with_key(counterparty: str, amount_usdc: float, amount: int, m) -> dict:
    """Same USDC transfer, signed locally. No portal, no account, no SDK keys."""
    from eth_account import Account
    from web3 import Web3

    acct = Account.from_key(os.environ["NERACA_STAKE_KEY"])
    vault = _vault_address(acct.address)
    w3 = Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC))
    tx = {
        "to": Web3.to_checksum_address(USDC_SEPOLIA),
        "data": _erc20_transfer_data(vault, amount),
        "chainId": 84532,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
        "gas": 100_000,
    }
    signed = acct.sign_transaction(tx)
    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    except Exception as e:
        raise SystemExit(f"stake did not broadcast: {e} - is {acct.address} funded with "
                         "Base Sepolia ETH for gas and USDC to stake? "
                         "`python -m neraca.onchain wallet` prints both balances")
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash
    m.write_event(acted=[f"staked {amount_usdc} USDC guarantee on {counterparty}"],
                  extra={"kind": "guarantee_stake", "counterparty": counterparty,
                         "amount_usdc": amount_usdc, "tx": tx_hash})
    return {"tx": tx_hash, "explorer": BASESCAN + tx_hash,
            "from": acct.address, "vault": vault, "amount_usdc": amount_usdc}


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
        if os.environ.get("CDP_API_KEY_ID") and not os.environ.get("NERACA_STAKE_KEY"):
            print(json.dumps(asyncio.run(wallet()), indent=2))
        else:
            out = local_wallet()
            if out.get("funded") is not False:
                print(json.dumps(out, indent=2, default=str))
    elif cmd == "stake":
        print(json.dumps(asyncio.run(stake_guarantee(sys.argv[2], float(sys.argv[3]))), indent=2))
    else:
        raise SystemExit("usage: python -m neraca.onchain [b20|wallet|stake <counterparty> <usdc>]")


if __name__ == "__main__":
    main()
