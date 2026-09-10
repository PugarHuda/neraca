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
    if not vault:
        # you brought your own key; the escrow side just needs an address to receive
        fresh = Account.create()
        print(f"No vault set. Paste this into .env:{chr(10)}")
        print(f"NERACA_VAULT={fresh.address}")
        print(f"NERACA_BUYER_KEY={fresh.key.hex()}   # doubles as the x402 buyer{chr(10)}")
        vault = fresh.address
    return {"staking_wallet": acct.address, "balances": balances(acct.address),
            "vault": vault, "vault_balances": balances(vault)}


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
    from . import makelar
    from .memory import client, norm
    m = client()
    counterparty = norm(counterparty)
    body = (m.get_state(f"negotiation:{counterparty}") or {}).get("body") or {}
    verdict = body.get("verdict")
    if verdict != "APPROVE_WITH_GUARANTEE":
        raise SystemExit(f"no open APPROVE_WITH_GUARANTEE negotiation for {counterparty} "
                         f"(found: {verdict}) - the stake is priced by memory, not typed by hand")
    # an open negotiation is necessary, not sufficient: memory may have moved
    # since it opened. Re-decide against the journal as it stands right now.
    fresh = makelar.decide(counterparty, body.get("budget") or amount_usdc, m)
    if fresh["verdict"] != "APPROVE_WITH_GUARANTEE":
        raise SystemExit(f"memory moved since the negotiation on {counterparty} opened: it now says "
                         f"{fresh['verdict']} ({fresh['reasons']}) - refusing to stake on a stale verdict")

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


# ---- ERC-8004 Trustless Agents: portable, on-chain reputation ----------------
# Reference deployments on Base Sepolia (erc-8004/erc-8004-contracts).
ERC8004_IDENTITY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"
ERC8004_REPUTATION = "0x8004B663056A597Dffe9eCcC1965A193B7388713"
IDENTITY_KEY = "neraca:erc8004-identity"   # HOT: our agentId once registered
_IDENTITY_ABI = [
    {"type": "function", "name": "register", "stateMutability": "nonpayable",
     "inputs": [{"name": "agentURI", "type": "string"}], "outputs": [{"name": "agentId", "type": "uint256"}]},
    {"type": "function", "name": "ownerOf", "stateMutability": "view",
     "inputs": [{"name": "tokenId", "type": "uint256"}], "outputs": [{"name": "", "type": "address"}]},
    {"type": "event", "name": "Registered", "anonymous": False,
     "inputs": [{"name": "agentId", "type": "uint256", "indexed": True},
                {"name": "agentURI", "type": "string", "indexed": False},
                {"name": "owner", "type": "address", "indexed": True}]},
]
_REPUTATION_ABI = [
    {"type": "function", "name": "giveFeedback", "stateMutability": "nonpayable",
     "inputs": [{"name": "agentId", "type": "uint256"}, {"name": "value", "type": "int128"},
                {"name": "valueDecimals", "type": "uint8"}, {"name": "tag1", "type": "string"},
                {"name": "tag2", "type": "string"}, {"name": "endpoint", "type": "string"},
                {"name": "feedbackURI", "type": "string"}, {"name": "feedbackHash", "type": "bytes32"}],
     "outputs": []},
    {"type": "function", "name": "getSummary", "stateMutability": "view",
     "inputs": [{"name": "agentId", "type": "uint256"}, {"name": "clientAddresses", "type": "address[]"},
                {"name": "tag1", "type": "string"}, {"name": "tag2", "type": "string"}],
     "outputs": [{"name": "count", "type": "uint64"}, {"name": "summaryValue", "type": "int128"},
                 {"name": "summaryValueDecimals", "type": "uint8"}]},
]


def _sepolia_signer(which: str = "stake"):
    """'stake' is NERACA's own key; 'buyer' is the demo counterparty's, so a
    second identity can be registered by a different owner."""
    from eth_account import Account
    from web3 import Web3
    var = {"stake": "NERACA_STAKE_KEY", "buyer": "NERACA_BUYER_KEY"}[which]
    key = os.environ.get(var)
    if not key:
        raise SystemExit(f"set {var} (a funded Base Sepolia key) - ERC-8004 needs a signer")
    return Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC)), Account.from_key(key)


def _send(w3, acct, fn) -> str:
    tx = fn.build_transaction({
        "from": acct.address, "chainId": 84532,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "maxFeePerGas": w3.eth.gas_price * 2, "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
    })
    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    h = h if h.startswith("0x") else "0x" + h
    rc = w3.eth.wait_for_transaction_receipt(h, timeout=120)
    if rc.status != 1:
        raise SystemExit(f"transaction reverted: {BASESCAN}{h}")
    return h


def erc8004_identity(agent_uri: str = "https://github.com/PugarHuda/neraca", signer: str = "stake") -> dict:
    """Register an ERC-8004 agent on Base Sepolia (once per signer).

    signer='stake' registers NERACA itself; signer='buyer' registers the demo
    counterparty under a different owner, so feedback about it is not
    self-feedback. The agentId is remembered in HOT state; a second call
    returns it instead of minting again.
    """
    from .memory import client
    m = client()
    key = IDENTITY_KEY if signer == "stake" else f"{IDENTITY_KEY}:{signer}"
    known = (m.get_state(key) or {}).get("body")
    if known:
        return known | {"already_registered": True}
    w3, acct = _sepolia_signer(signer)
    identity = w3.eth.contract(address=ERC8004_IDENTITY, abi=_IDENTITY_ABI)
    tx = _send(w3, acct, identity.functions.register(agent_uri))
    from web3.logs import DISCARD  # the receipt also carries ERC-721 Transfer/MetadataSet logs
    rc = w3.eth.get_transaction_receipt(tx)
    agent_id = identity.events.Registered().process_receipt(rc, errors=DISCARD)[0]["args"]["agentId"]
    out = {"agent_id": agent_id, "owner": acct.address, "agent_uri": agent_uri,
           "tx": tx, "explorer": BASESCAN + tx, "registry": ERC8004_IDENTITY}
    m.set_state(key, out)
    m.write_event(acted=[f"registered ERC-8004 identity {agent_id}"],
                  extra={"kind": "erc8004_identity", **out})
    return out


def erc8004_feedback(agent_id: int, budget: float = 50.0) -> dict:
    """Publish NERACA's verdict on an ERC-8004 agent as on-chain reputation.

    The subject is whoever owns the agentId. The feedback IS the memory-backed
    score: no remembered history, nothing to publish - the bureau does not
    rate strangers. Value is the score (0-100), tag1 the verdict, tag2 the
    rubric version it was decided under, so the reputation is auditable.
    """
    from . import makelar
    from .memory import client, get_rubric
    m = client()
    w3, acct = _sepolia_signer()
    identity = w3.eth.contract(address=ERC8004_IDENTITY, abi=_IDENTITY_ABI)
    subject = identity.functions.ownerOf(agent_id).call()
    decision = makelar.decide(subject, budget, m)
    if decision["verdict"] == makelar.NO_HISTORY:
        raise SystemExit(f"agent {agent_id} is owned by {subject}, and NERACA remembers nothing "
                         "about it - the bureau does not rate strangers")
    if subject.lower() == acct.address.lower():
        raise SystemExit("ERC-8004 forbids self-feedback: the subject is our own signer")
    reputation = w3.eth.contract(address=ERC8004_REPUTATION, abi=_REPUTATION_ABI)
    digest = w3.keccak(text=json.dumps(decision, sort_keys=True))
    tx = _send(w3, acct, reputation.functions.giveFeedback(
        agent_id, int(decision["score"]), 0, decision["verdict"],
        f"rubric-v{get_rubric(m).get('version', 1)}",
        "", "", digest))
    count, value, dec = reputation.functions.getSummary(agent_id, [acct.address], "", "").call()
    out = {"agent_id": agent_id, "subject": subject, "score": decision["score"],
           "verdict": decision["verdict"], "tx": tx, "explorer": BASESCAN + tx,
           "on_chain_summary": {"count": count, "value": value, "decimals": dec}}
    m.write_event(acted=[f"published ERC-8004 feedback on agent {agent_id}"],
                  extra={"kind": "erc8004_feedback", **out})
    return out


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
    elif cmd == "identity":
        print(json.dumps(erc8004_identity(*sys.argv[2:4]), indent=2))
    elif cmd == "feedback":
        print(json.dumps(erc8004_feedback(int(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 50.0),
                         indent=2, default=str))
    else:
        raise SystemExit("usage: python -m neraca.onchain [b20|wallet|stake <counterparty> <usdc>"
                         "|identity [agentURI]|feedback <agentId> [budget]]")


if __name__ == "__main__":
    main()
