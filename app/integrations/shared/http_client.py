import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from typing import Optional

def get_http_client(
    timeout: float = 10.0,
    base_url: Optional[str] = None,
    headers: Optional[dict] = None
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        headers=headers or {},
        timeout=httpx.Timeout(timeout=timeout)
    )


def retry_decorator(
    stop_after: int = 3,
    wait_multiplier: float = 1.0,
    wait_min: float = 1.0,
    wait_max: float = 8.0
):
    return retry(
        stop=stop_after_attempt(stop_after),
        wait=wait_exponential(multiplier=wait_multiplier, min=wait_min, max=wait_max),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
