"""NERACA - the trust bureau for the agent economy.

Credentials live in .env (see .env.example). Load them once here, so every
entry point - the CLI, the x402 storefront, the ACP seller, the on-chain arm -
sees the same environment. Real env vars always win over the file.
"""

from dotenv import load_dotenv

load_dotenv()
