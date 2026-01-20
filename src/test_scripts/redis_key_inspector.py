"""Utility script to inspect key counts in the configured Redis instance."""

import os
import sys

import redis


def get_redis_client() -> redis.Redis:
    """Build a Redis client from environment variables."""
    host = os.getenv("REDIS_HOST")
    port = os.getenv("REDIS_PORT", "6379")
    password = os.getenv("REDIS_PASSWORD")
    use_ssl = os.getenv("REDIS_USE_SSL", "true").lower() == "true"

    if not host:
        raise RuntimeError("REDIS_HOST must be set")

    try:
        port_int = int(port)
    except ValueError as exc:
        raise RuntimeError(f"Invalid REDIS_PORT '{port}'") from exc

    return redis.StrictRedis(
        host=host,
        port=port_int,
        password=password,
        ssl=use_ssl,
        decode_responses=True,
    )


def main(limit: int = 50) -> int:
    client = get_redis_client()
    client.ping()

    total_keys = client.dbsize()
    print(f"Total keys: {total_keys}")

    print(f"First {limit} keys:")
    count = 0
    for key in client.scan_iter(count=limit):
        print(f"  {key}")
        count += 1
        if count >= limit:
            break

    if count == 0:
        print("  (no keys returned)")

    return 0


if __name__ == "__main__":
    limit_arg = 50
    if len(sys.argv) > 1:
        try:
            limit_arg = int(sys.argv[1])
        except ValueError:
            print(f"Invalid limit '{sys.argv[1]}', using default 50", file=sys.stderr)
    raise SystemExit(main(limit_arg))
