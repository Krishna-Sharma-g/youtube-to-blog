import asyncio, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from utils.youtube_processor import fetch_transcript   # async now
from utils.openai_client    import chat

async def main(url: str):
    print(f"[+] Fetching captions for: {url}")
    full_txt = await fetch_transcript(url)
    snippet  = full_txt[:1_000]
    print(f"[+] Got {len(snippet)} characters; sending to OpenAI…")

    summary = await chat(
        [{"role": "user",
          "content": f"Summarize in exactly three sentences:\n{snippet}"}],
        max_tokens=120,
    )

    print("\n=== SUMMARY ===\n")
    print(summary)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_test.py \"<YouTube URL>\"")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
