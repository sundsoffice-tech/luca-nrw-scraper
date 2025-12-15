import os
import httpx

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080")

async def searxng_search(query: str, timeout: float = 8.0, limit: int = 10):
    url = f"{SEARXNG_URL.rstrip('/')}/search"
    params = {
        "q": query,
        "format": "json",
        "language": "de",
        "safesearch": 0,
        "pageno": 1,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])[:limit]
        return [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("content"),
                "engine": item.get("engine"),
            }
            for item in results
        ]