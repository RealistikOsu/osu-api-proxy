from __future__ import annotations

from typing import Any
from typing import Optional
import asyncio
import random
import logging

from aiohttp import web
import aiohttp

from config import config


# Auth
def get_oapi_key() -> str:
    return random.choice(config.oapi_key_pool)

def compare_access_key(access_key: Optional[str]) -> bool:
    if not config.app_access_key:
        return True
    
    return access_key == config.app_access_key

# HTTP Client
session: aiohttp.ClientSession
OAPI_BASE = "https://old.ppy.sh/api"

async def send_api_request(
    endpoint: str,
    params: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    params["k"] = get_oapi_key()
    url = f"{OAPI_BASE}/{endpoint}"
    async with session.get(url, params=params) as response:
        return response.status, await response.json()

# HTTP Server
async def handle_connection(request: web.Request) -> web.Response:
    if not str(request.path).startswith(config.http_prefix):
        return web.Response(status=404)

    if not compare_access_key(request.query.get("k")):
        return web.Response(status=403)

    endpoint = str(request.path).removeprefix(config.http_prefix)
    params = dict(request.query)

    try:
        status, data = await send_api_request(endpoint, params)
    except aiohttp.ClientError:
        return web.Response(status=500)

    return web.json_response(data, status=status)


async def main() -> int:
    # Config check
    if not config.oapi_key_pool:
        logging.error("No osu!api keys present in the pool. Cannot continue.")
        return 1

    if not config.app_access_key:
        logging.warning("No app access key set. Anyone can use this API.")

    # HTTP Client
    global session
    session = aiohttp.ClientSession()

    runner = web.ServerRunner(
        web.Server(handle_connection) # type: ignore
    )
    await runner.setup()
    site = web.TCPSite(runner, config.http_host, config.http_port)
    await site.start()
    logging.info(f"Server started on {config.http_host}:{config.http_port}")
    
    # Keep the server running
    while True:
        await asyncio.sleep(100)
    
    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    raise SystemExit(
        asyncio.run(main())
    )
