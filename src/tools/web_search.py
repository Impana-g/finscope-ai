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
            raise ValueError(
                "TAVILY_API_KEY not set in .env"
            )

        _client = TavilyClient(api_key=api_key)

    return _client


def web_search(query: str, max_results: int = 5):

    for attempt in range(3):

        try:

            client = get_tavily()

            result = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )

            sources = []
            content_parts = []

            for r in result.get("results", []):

                sources.append(r.get("url", ""))

                content_parts.append(
                    f"Source: {r.get('url', '')}\n"
                    f"Title: {r.get('title', '')}\n"
                    f"Content: {r.get('content', '')}"
                )

            full_content = "\n\n---\n\n".join(
                content_parts
            )

            return {
                "success": True,
                "query": query,
                "content": full_content,
                "sources": sources,
                "result_count": len(sources)
            }

        except Exception as e:

            print(
                f"Search attempt {attempt + 1} failed: {e}"
            )

            if attempt < 2:

                wait = 2 ** attempt

                print(f"Retrying in {wait}s...")

                time.sleep(wait)

            else:

                return {
                    "success": False,
                    "query": query,
                    "content": "",
                    "sources": [],
                    "error": str(e)
                }


if __name__ == "__main__":

    print("Testing web search...")

    result = web_search(
        "Infosys financial results 2025"
    )

    if result["success"]:

        print(
            f"✅ Found {result['result_count']} results"
        )

        print(
            f"First source: {result['sources'][0]}"
        )

    else:

        print(
            f"❌ Search failed: {result.get('error')}"
        )