"""
Swarms World API tools: launch a token and claim fees.

These functions call the Swarms World HTTP APIs using httpx. They are intended
for use as agent tools (e.g. passed to swarms.Agent(tools=[...])).
"""

from __future__ import annotations

import json
import os

import httpx

DEFAULT_BASE_URL = "https://swarms.world"

_ENV_PRIVATE_KEY = "WALLET_PRIVATE_KEY"
_ENV_API_KEY = "SWARMS_API_KEY"


def _get_private_key() -> str:
    """
    Retrieve the Swarms World wallet private key from the environment.

    Returns:
        str: The private key string.

    Raises:
        ValueError: If the private key is not set in the environment as WALLET_PRIVATE_KEY.

    Notes:
        The private key is required to sign token launch or fee claim requests to the Swarms World API.
        It should be set in your .env file or the process environment as WALLET_PRIVATE_KEY.
    """
    key = os.environ.get(_ENV_PRIVATE_KEY, "").strip()
    if not key:
        raise ValueError(
            f"Wallet private key required: set {_ENV_PRIVATE_KEY} in .env"
        )
    return key


def _get_api_key() -> str:
    """
    Retrieve the Swarms World API key from the environment.

    Returns:
        str: The API key string.

    Raises:
        ValueError: If the API key is not set in the environment as SWARMS_API_KEY.

    Notes:
        The API key is required to authenticate with the Swarms World HTTP API endpoints.
        It should be set in your .env file or the process environment as SWARMS_API_KEY.
    """
    key = os.environ.get(_ENV_API_KEY, "").strip()
    if not key:
        raise ValueError(
            f"API key required: set {_ENV_API_KEY} in .env"
        )
    return key


def launch_token(
    name: str,
    description: str,
    ticker: str,
    image: str | None = None,
) -> str:
    """
    Create a minimal agent listing and launch an associated token on Solana.

    Calls POST {base_url}/api/token/launch. Requires an API key (Bearer).
    Token creation costs approximately 0.04 SOL from the wallet associated
    with the private key. The wallet private key is read from the environment
    (WALLET_PRIVATE_KEY in .env).

    Args:
        name: Display name of the agent (min 2 characters).
        description: Description of the agent (non-empty).
        ticker: Token symbol, 1–10 letters/numbers (e.g. MAG, SWARM). Uppercased.
        image: Optional agent/token image: URL, or base64/data URL. Omit for no image.
        api_key: Swarms World API key. Defaults to env SWARMS_API_KEY.
        base_url: API base URL. Defaults to https://swarms.world.
        timeout: Request timeout in seconds.

    Returns:
        JSON string of the API result (success, id, listing_url, tokenized,
        token_address, pool_address). On non-2xx: raises httpx.HTTPStatusError.

    Example:
        >>> result = launch_token("My Agent", "An agent.", "MAG")
        >>> print(result)
    """

    key = _get_api_key()
    base_url = DEFAULT_BASE_URL
    timeout = 60.0

    payload = {
        "name": name,
        "description": description,
        "ticker": ticker,
        "private_key": _get_private_key(),
    }

    if image is not None:
        payload["image"] = image

    with httpx.Client(timeout=timeout) as client:
        url = f"{base_url.rstrip('/')}/api/token/launch"
        response = client.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response.status_code >= 400:
            req = response.request or httpx.Request("POST", url)
            raise httpx.HTTPStatusError(
                "HTTP error launching token",
                request=req,
                response=response,
            )
        return json.dumps(response.json())


def claim_fees(
    ca: str,
) -> str:
    """
    Claim accumulated fees for a token on Solana.

    Calls POST {base_url}/api/product/claimfees. The private key is read from
    the environment (WALLET_PRIVATE_KEY in .env), used only to sign the
    claim transaction, and is not stored. No API key required.

    Args:
        ca: Token mint / contract address (Solana, 32–44 characters).
        base_url: API base URL. Defaults to https://swarms.world.
        timeout: Request timeout in seconds.

    Returns:
        JSON string of the API result (success, signature, amountClaimedSol,
        fees). On non-2xx: raises httpx.HTTPStatusError.

    Example:
        >>> result = claim_fees("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
        >>> print(result)
    """
    base_url = DEFAULT_BASE_URL
    timeout = 60.0

    payload = {
        "ca": ca,
        "privateKey": _get_private_key(),
    }

    with httpx.Client(timeout=timeout) as client:
        url = f"{base_url.rstrip('/')}/api/product/claimfees"
        response = client.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        if response.status_code >= 400:
            req = response.request or httpx.Request("POST", url)
            raise httpx.HTTPStatusError(
                "HTTP error claiming fees",
                request=req,
                response=response,
            )
        return json.dumps(response.json())
