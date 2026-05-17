"""
http_client.py
==============
Thin, retry-aware HTTP session wrapper built on top of requests + urllib3.
All requests go through this module so retry / header logic is centralised.
"""

import random
import time
from typing import Optional

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter

from urllib3.util.retry import Retry

from config import (
    DELAY_BETWEEN_REQUESTS,
    REQUEST_TIMEOUT,
    RETRY_ATTEMPTS,
    RETRY_BACKOFF,
    USER_AGENTS,
)
from utils import setup_logger

logger = setup_logger()


def _build_session() -> Session:
    """
    Create a requests.Session pre-configured with:
    - Connection-level retries (via HTTPAdapter)
    - Random User-Agent rotation
    """
    session = requests.Session()

    retry = Retry(
        total=RETRY_ATTEMPTS,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://",  adapter)
    session.mount("https://", adapter)
    return session


# Module-level singleton session
_SESSION: Optional[Session] = None


def get_session() -> Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = _build_session()
    return _SESSION


def _random_headers() -> dict:
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",   # no brotli — requests can't decode br natively
        "Connection":      "keep-alive",
        "DNT":             "1",
        "Upgrade-Insecure-Requests": "1",
    }


def fetch(url: str, stream: bool = False) -> Optional[Response]:
    """
    Fetch a URL with retry logic, polite delay, and rotating User-Agent.

    Returns a Response object on success or None on failure.
    """
    session = get_session()
    headers = _random_headers()

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            time.sleep(DELAY_BETWEEN_REQUESTS)
            resp = session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                stream=stream,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                return resp
                
            if resp.status_code in (401, 403, 404):
                logger.warning("HTTP %s for %s — skipping", resp.status_code, url)
                return None

            logger.warning(
                "HTTP %s for %s (attempt %d/%d)",
                resp.status_code, url, attempt, RETRY_ATTEMPTS,
            )
        except requests.exceptions.SSLError:
            logger.warning("SSL error on %s — skipping", url)
            return None
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Connection error on %s: %s (attempt %d/%d)", url, exc, attempt, RETRY_ATTEMPTS)
        except requests.exceptions.Timeout:
            logger.warning("Timeout on %s (attempt %d/%d)", url, attempt, RETRY_ATTEMPTS)
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed for %s: %s", url, exc)
            return None

        wait = RETRY_BACKOFF * (2 ** (attempt - 1))
        logger.debug("Waiting %.1fs before retry…", wait)
        time.sleep(wait)

    logger.error("Exhausted retries for %s", url)
    return None
