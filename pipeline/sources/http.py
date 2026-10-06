"""HTTP helpers with retry and exponential backoff."""

import logging
import time

import requests

log = logging.getLogger(__name__)

USER_AGENT = "grzyby-pipeline/0.1 (private, non-commercial)"


def get(url: str, params: dict | None = None, timeout: int = 180, retries: int = 5) -> requests.Response:
    """GET with retries on network errors and 429/5xx responses."""
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            if attempt == retries:
                raise
            wait = 2 ** (attempt + 1)
            log.warning("GET %s failed (%s), retry in %ss", url, exc, wait)
            time.sleep(wait)
    raise AssertionError("unreachable")
