import json
import logging

from urllib3 import PoolManager, Retry

DEFAULT_TIMEOUT = 2.0
DEFAULT_RETRIES = 3

http = PoolManager()


def try_request(
        url,
        timeout=DEFAULT_TIMEOUT,
        retries=DEFAULT_RETRIES,
        headers=None,
        log_exception=True
):
    retries = Retry(connect=retries, read=retries, redirect=5, backoff_factor=0.1)
    try:
        response = http.request(
            "GET",
            url,
            timeout=timeout,
            retries=retries,
            headers=headers
        )
        return response.data
    except Exception:
        logger = logging.exception if log_exception else logging.warning
        logger(f"GET failed: {url}")
        return None


def try_json_request(url, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    data = try_request(url, timeout, retries)
    try:
        return json.loads(data)
    except Exception:
        logging.exception(f"Parsing JSON failed from {url}")
        return None
