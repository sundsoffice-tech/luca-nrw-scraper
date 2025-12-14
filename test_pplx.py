import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Lade .env
load_dotenv()

async def test_perplexity():
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ FEHLER: Kein PERPLEXITY_API_KEY in der .env gefunden!")
        return

    # Key maskieren für Anzeige
    masked_key = api_key[:5] + "..." + api_key[-4:] if len(api_key) > 10 else "N/A"
    print(f"🔑 Key gefunden: {masked_key}")
    print("🚀 Sende Test-Anfrage an Perplexity (Sonar)...")

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Wir fragen nach URLs, um die Extraction zu testen
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. List 3 URLs of German solar sales companies."},
            {"role": "user", "content": "Gib mir 3 Webseiten von Solar-Vertriebsfirmen in Deutschland."}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data['choices'][0]['message']['content']
                    citations = data.get('citations', [])

                    print("\n✅ ERFOLG! Antwort erhalten:")
                    print("-" * 40)
                    print(content)
                    print("-" * 40)
                    print(f"\n🔗 Gefundene Citations (URLs): {len(citations)}")
                    for c in citations:
                        print(f"   - {c}")
                else:
                    error_text = await resp.text()
                    print(f"\n❌ API FEHLER: Status {resp.status}")
                    print(f"Details: {error_text}")
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")

if __name__ == "__main__":
    asyncio.run(test_perplexity())
