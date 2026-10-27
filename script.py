import os
import time
import requests

IDS = [1342, 11]
DOSSIER = "livres_en"
HEADERS = {"User-Agent": "TantaraBot/1.0 (fampiasana manokana)"}
os.makedirs(DOSSIER, exist_ok=True)

for bid in IDS:
    # 1. Metadata avy amin'ny Gutendex (lisansa + lohateny)
    titre, lisansa = f"boky_{bid}", "Tsy fantatra"
    try:
        r = requests.get(f"https://gutendex.com/books/{bid}", headers=HEADERS, timeout=60)
        if r.status_code == 200:
            b = r.json()
            titre = b.get("title", titre)
            lisansa = "Domaine public" if b.get("copyright") is False else "Mety misy alalana"
    except requests.RequestException as e:
        print(f"Gutendex tsy mandeha ho an'ny {bid}: {e}")

    print(f"Boky {bid}: {titre} | Lisansa: {lisansa}")

    # 2. Fampidinana TXT mivantana avy amin'ny Gutenberg
    url = f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.txt"
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
        r.raise_for_status()
        chemin = os.path.join(DOSSIER, f"{bid}.txt")
        with open(chemin, "wb") as f:
            f.write(r.content)
        print(f"  Voaray: {chemin} ({len(r.content) // 1024} KB)")
    except requests.RequestException as e:
        print(f"  Tsy nahomby: {e}")

    time.sleep(3)
