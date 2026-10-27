import os
import time
import requests

IDS = [13765, 24867]
DOSSIER = "livres"
HEADERS = {"User-Agent": "TantaraBot/1.0 (fampiasana manokana)"}
os.makedirs(DOSSIER, exist_ok=True)

for bid in IDS:
    url = f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.txt"
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
        r.raise_for_status()
        chemin = os.path.join(DOSSIER, f"{bid}.txt")
        with open(chemin, "wb") as f:
            f.write(r.content)
        print(f"Voaray: {chemin} ({len(r.content) // 1024} KB)")
    except requests.RequestException as e:
        print(f"Tsy nahomby ho an'ny {bid}: {e}")
    time.sleep(3)
