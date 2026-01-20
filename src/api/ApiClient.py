import time

import httpx

from api.config.config import logger


class ApiClient:
    """
    A basic API client for making HTTP requests with retry logic.
    """

    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=timeout)

    def post(self, endpoint: str, data: dict, max_retries: int = 3, backoff_factor: float = 0.5) -> httpx.Response:
        url = f"{self.base_url}{endpoint}"
        retries = 0
        while retries <= max_retries:
            try:
                logger.info(f"Attempt {retries + 1}/{max_retries + 1} for POST {url}")
                response = self.client.post(url, json=data)
                response.raise_for_status()  # Raise an exception for 4xx/5xx responses
                logger.info(f"POST request to {url} successful.")
                return response
            except httpx.HTTPStatusError as e:
                if 500 <= e.response.status_code < 600:
                    logger.error(f"Server error ({e.response.status_code}) for {url}. Retrying...")
                    retries += 1
                    if retries <= max_retries:
                        sleep_time = backoff_factor * (2 ** (retries - 1))
                        logger.info(f"Waiting for {sleep_time:.2f} seconds before next retry...")
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"Max retries ({max_retries}) exceeded for {url}. Last error: {e}")
                        raise  # Re-raise the last exception if retries are exhausted
                else:
                    logger.error(f"Client error or unretriable server error ({e.response.status_code}) for {url}.")
                    raise  # Re-raise for non-5xx errors
            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {e}. Retrying...")
                retries += 1
                if retries <= max_retries:
                    sleep_time = backoff_factor * (2 ** (retries - 1))
                    logger.info(f"Waiting for {sleep_time:.2f} seconds before next retry...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Max retries ({max_retries}) exceeded for {url}. Last error: {e}")
                    raise  # Re-raise network errors if retries are exhausted

        # This part should ideally not be reached if exceptions are always raised
        raise Exception("Unexpected error: POST request failed without raising an exception.")

    def close(self):
        self.client.close()
        logger.info("httpx client closed.")
