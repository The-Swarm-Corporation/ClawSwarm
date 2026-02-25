"""
Swarms World API tools: launch a token and claim fees.

These functions call the Swarms World HTTP APIs using httpx. They are
intended for use as agent tools (e.g. passed to swarms.Agent(tools=[...])).

Token Launch API docs:
  https://docs.swarms.ai/en/latest/swarms_platform/token_api/
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from loguru import logger

DEFAULT_BASE_URL = "https://swarms.world"
_API_KEYS_URL = "https://swarms.world/platform/api-keys"

_ENV_PRIVATE_KEY = "WALLET_PRIVATE_KEY"
_ENV_API_KEY = "SWARMS_API_KEY"


def _get_private_key() -> str:
    """
    Retrieve the Swarms World wallet private key from the environment.

    Accepted formats: JSON array of 64 bytes, base64, or base58.

    Raises:
        ValueError: If WALLET_PRIVATE_KEY is not set.
    """
    key = (
        os.environ.get(_ENV_PRIVATE_KEY, "")
        .strip()
        .strip('"')
        .strip("'")
    )
    if not key:
        raise ValueError(
            f"Wallet private key required: set {_ENV_PRIVATE_KEY} in .env"
        )
    return key


def _get_api_key() -> str:
    """
    Retrieve the Swarms World API key from the environment.

    Create or manage keys at https://swarms.world/platform/api-keys.

    Raises:
        ValueError: If SWARMS_API_KEY is not set.
    """
    key = os.environ.get(_ENV_API_KEY, "").strip()
    # Strip surrounding quotes that some .env editors leave in the file
    # (e.g.  SWARMS_API_KEY="sk-..."  →  value includes literal quote chars
    # if the dotenv parser does not handle them).
    key = key.strip('"').strip("'")
    if not key:
        raise ValueError(
            f"API key required: set {_ENV_API_KEY} in .env  "
            f"Get one at {_API_KEYS_URL}"
        )
    return key


def _log_api_error(
    fn: str, status: int, url: str, body: dict
) -> None:
    """Emit a structured error log matched to the known API error shapes."""
    error = body.get("error", "unknown")
    message = body.get("message", "")

    if status == 401:
        keys_url = body.get("how_to_get_key", _API_KEYS_URL)
        logger.error(
            "{}: authentication failed | status=401 error={!r} "
            "message={!r}  →  get/check your key at {}",
            fn,
            error,
            message,
            keys_url,
        )
    elif status == 400:
        details = body.get("details", "")
        field_errors = (
            details.get("fieldErrors", {})
            if isinstance(details, dict)
            else details
        )
        logger.error(
            "{}: bad request | status=400 error={!r} "
            "message={!r} field_errors={}",
            fn,
            error,
            message,
            field_errors,
        )
    elif status == 405:
        logger.error(
            "{}: method not allowed | status=405 url={}", fn, url
        )
    elif status == 429:
        usage = body.get("currentUsage", "?")
        reset = body.get("resetTime", "unknown")
        logger.error(
            "{}: rate limit exceeded | status=429 "
            "current_usage={} resets_at={!r}",
            fn,
            usage,
            reset,
        )
    elif status == 500:
        logger.error(
            "{}: server error | status=500 error={!r} "
            "message={!r} url={}",
            fn,
            error,
            message,
            url,
        )
    else:
        logger.error(
            "{}: API error | status={} error={!r} "
            "message={!r} url={}",
            fn,
            status,
            error,
            message,
            url,
        )


def launch_token(
    name: str,
    description: str,
    ticker: str,
    image: str | None = None,
    image_path: str | None = None,
) -> str:
    """
    Create a minimal agent listing and launch an associated token on Solana.

    Calls POST https://swarms.world/api/token/launch.
    Token creation costs approximately 0.04 SOL from the wallet associated
    with the private key. SWARMS_API_KEY and WALLET_PRIVATE_KEY must be
    set in the environment or .env file.

    Args:
        name: Display name of the agent. Minimum 2 characters.
        description: Description of the agent. Cannot be empty.
        ticker: Token symbol, 1–10 letters/numbers (e.g. MAG, SWARM).
            Automatically uppercased by the API.
        image: Optional image as a URL (https://...) or base64 / data URL.
            Sent via JSON body. Ignored when image_path is also provided.
        image_path: Optional path to a local image file (PNG, JPEG, WebP,
            GIF). When provided the request is sent as multipart/form-data
            so the raw bytes are uploaded. Takes precedence over image.

    Returns:
        JSON string with fields: success, id, listing_url, tokenized,
        token_address, pool_address.

    Raises:
        ValueError: If SWARMS_API_KEY or WALLET_PRIVATE_KEY are not set.
        FileNotFoundError: If image_path is provided but the file is missing.
        httpx.HTTPStatusError: On any 4xx / 5xx response from the API.
        httpx.TimeoutException: If the request exceeds 60 s.
        httpx.RequestError: On DNS / connection-level failures.

    Private key formats accepted:
        - JSON array of 64 bytes:  "[1,2,3,...,64]"
        - Base64-encoded 64-byte key
        - Base58-encoded key (e.g. Phantom export format)

    Examples:
        >>> result = launch_token("My Agent", "An agent.", "MAG")
        >>> result = launch_token(
        ...     "My Agent", "An agent.", "MAG",
        ...     image="https://example.com/icon.png",
        ... )
        >>> result = launch_token(
        ...     "My Agent", "An agent.", "MAG",
        ...     image_path="/path/to/icon.png",
        ... )
    """
    key = _get_api_key()
    private_key = _get_private_key()
    url = f"{DEFAULT_BASE_URL}/api/token/launch"
    timeout = 60.0

    # Masked key diagnostic — confirms the right value is loaded.
    # Logged at INFO (not DEBUG) so it appears regardless of log-level config.
    _key_preview = key[:6] + "..." if len(key) > 6 else "***"
    logger.info(
        "launch_token: SWARMS_API_KEY prefix={!r} len={} "
        "(wrong prefix? check .env for extra quotes or name typos)",
        _key_preview,
        len(key),
    )
    logger.info(
        "launch_token: POST {} | name={!r} ticker={!r} multipart={}",
        url,
        name,
        ticker,
        image_path is not None,
    )

    auth_headers = {"Authorization": f"Bearer {key}"}

    with httpx.Client(timeout=timeout) as client:
        try:
            if image_path is not None:
                # Multipart: raw file upload (PNG, JPEG, WebP, GIF, etc.)
                img = Path(image_path)
                if not img.is_file():
                    raise FileNotFoundError(
                        f"launch_token: image_path not found: {image_path}"
                    )
                logger.debug(
                    "launch_token: sending multipart | file={} size={}B",
                    img.name,
                    img.stat().st_size,
                )
                with img.open("rb") as fh:
                    response = client.post(
                        url,
                        headers=auth_headers,
                        data={
                            "name": name,
                            "description": description,
                            "ticker": ticker,
                            "private_key": private_key,
                        },
                        files={"image": (img.name, fh, "image/*")},
                    )
            else:
                # JSON: URL, base64, data URL, or no image
                payload: dict = {
                    "name": name,
                    "description": description,
                    "ticker": ticker,
                    "private_key": private_key,
                }
                if image is not None:
                    payload["image"] = image
                response = client.post(
                    url,
                    headers={
                        **auth_headers,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.TimeoutException:
            logger.error(
                "launch_token: timed out after {}s | url={}",
                timeout,
                url,
            )
            raise
        except httpx.RequestError as exc:
            logger.error(
                "launch_token: network error | url={} error={}",
                url,
                exc,
            )
            raise

        logger.debug(
            "launch_token: response status={} elapsed={}ms",
            response.status_code,
            int(response.elapsed.total_seconds() * 1000),
        )

        if response.status_code >= 400:
            try:
                err_body = response.json()
            except Exception:
                err_body = {"error": response.text[:500]}
            _log_api_error(
                "launch_token", response.status_code, url, err_body
            )
            req = response.request or httpx.Request("POST", url)
            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code} launching token: "
                f"{err_body.get('message', response.text[:200])}",
                request=req,
                response=response,
            )

        data = response.json()
        logger.success(
            "launch_token: success | id={} listing_url={} "
            "token_address={} pool_address={}",
            data.get("id", "n/a"),
            data.get("listing_url", "n/a"),
            data.get("token_address", "n/a"),
            data.get("pool_address", "n/a"),
        )
        return json.dumps(data)


def claim_fees(
    ca: str,
) -> str:
    """
    Claim accumulated fees for a token on Solana.

    Calls POST https://swarms.world/api/product/claimfees. The private key
    is read from the environment (WALLET_PRIVATE_KEY in .env), used only to
    sign the claim transaction. No API key required for this endpoint.

    Args:
        ca: Token mint / contract address (Solana, 32–44 characters).

    Returns:
        JSON string with: success, signature, amountClaimedSol, fees.

    Raises:
        ValueError: If WALLET_PRIVATE_KEY is not set.
        httpx.HTTPStatusError: On any 4xx / 5xx response.
        httpx.TimeoutException: If the request exceeds 60 s.
        httpx.RequestError: On network-level failures.

    Example:
        >>> result = claim_fees("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
    """
    url = f"{DEFAULT_BASE_URL}/api/product/claimfees"
    timeout = 60.0

    payload = {
        "ca": ca,
        "privateKey": _get_private_key(),
    }

    logger.info("claim_fees: POST {} | ca={!r}", url, ca)

    with httpx.Client(timeout=timeout) as client:
        try:
            response = client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
        except httpx.TimeoutException:
            logger.error(
                "claim_fees: timed out after {}s | url={}",
                timeout,
                url,
            )
            raise
        except httpx.RequestError as exc:
            logger.error(
                "claim_fees: network error | url={} error={}",
                url,
                exc,
            )
            raise

        logger.debug(
            "claim_fees: response status={} elapsed={}ms",
            response.status_code,
            int(response.elapsed.total_seconds() * 1000),
        )

        if response.status_code >= 400:
            try:
                err_body = response.json()
            except Exception:
                err_body = {"error": response.text[:500]}
            _log_api_error(
                "claim_fees", response.status_code, url, err_body
            )
            req = response.request or httpx.Request("POST", url)
            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code} claiming fees: "
                f"{err_body.get('message', response.text[:200])}",
                request=req,
                response=response,
            )

        data = response.json()
        logger.success(
            "claim_fees: success | ca={} amount_sol={}",
            ca,
            data.get("amountClaimedSol", "n/a"),
        )
        return json.dumps(data)
