from tavily import TavilyClient
from dotenv import load_dotenv
import os
import time

load_dotenv()

_client = None


def get_tavily():
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set in .env")
        _client = TavilyClient(api_key=api_key)
    return _client


def web_search(query: str, max_results: int = 5) -> dict:
    for attempt in range(3):
        try:
            client = get_tavily()
            result = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )

            sources       = []
            content_parts = []
            raw_results   = []

            for r in result.get("results", []):
                url     = r.get("url", "")
                title   = r.get("title", "")
                content = r.get("content", "")

                sources.append(url)
                content_parts.append(
                    f"Source: {url}\nTitle: {title}\nContent: {content}"
                )
                raw_results.append({
                    "url":     url,
                    "title":   title,
                    "content": content,
                })

            return {
                "success":      True,
                "query":        query,
                "content":      "\n\n---\n\n".join(content_parts),
                "sources":      sources,
                "result_count": len(sources),
                "raw_results":  raw_results,
            }

        except Exception as e:
            print(f"Search attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                wait = 2 ** attempt
                print(f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                return {
                    "success":     False,
                    "query":       query,
                    "content":     "",
                    "sources":     [],
                    "raw_results": [],
                    "error":       str(e),
                }