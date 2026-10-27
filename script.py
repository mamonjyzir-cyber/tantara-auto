import os
import re
import sys
import time
import requests
import pandas as pd

# ID-n'ny boky mivantana (azo ampiana na esorina)
IDS = [13765, 24867]

DOSSIER = "livres"
HEADERS = {"User-Agent": "TantaraBot/1.0 (fampiasana manokana)"}

FORMATS = {
    "epub": "application/epub+zip",
    "pdf": "application/pdf",
    "txt": "text/plain",
}

COLONNES = ["id", "lohateny", "mpanoratra", "mpamaky", "lohahevitra", "rohy", "fichiers", "commentaire"]

os.makedirs(DOSSIER, exist_ok=True)


def get(url, timeout=60):
    """Fangatahana miaraka amin'ny fanandramana indray raha 429 na hadisoana server."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r
            print(f"Status {r.status_code} ho an'ny {url}")
            if r.status_code not in (429, 500, 502, 503, 504):
                return None
        except requests.RequestException as e:
            print(f"Hadisoana fifandraisana: {e}")
        time.sleep(5 * (attempt + 1))
    return None


def nom_fichier(texte):
    return re.sub(r"[^\w\-]+", "_", texte)[:80].strip("_") or "boky"


rows = []

for bid in IDS:
    r = get(f"https://gutendex.com/books/{bid}", timeout=30)
    if r is None:
        print(f"Tsy nahazo ny boky {bid}")
        continue

    b = r.json()
    titre = b.get("title", "")
    print(f"Boky {bid}: {titre}")

    auteurs = ", ".join(a.get("name", "") for a in b.get("authors", [])) or "Tsy fantatra"
    sujets = b.get("subjects", [])[:2]
    mpamaky = b.get("download_count", 0)
    formats = b.get("formats", {})

    commentaire = f"Malaza amin'ny mpamaky {mpamaky:,} ; mpanoratra: {auteurs}"
    if sujets:
        commentaire += f" ; lohahevitra: {'; '.join(sujets)}"

    fichiers = []
    for ext, mime in FORMATS.items():
        lien = next((u for k, u in formats.items() if k.startswith(mime)), None)
        if not lien:
            print(f"  Tsy misy {ext} ho an'ny {bid}")
            continue

        chemin = os.path.join(DOSSIER, f"{bid}_{nom_fichier(titre)}.{ext}")
        fichier = get(lien, timeout=120)
        if fichier is None:
            print(f"  Tsy nahomby: {ext} ho an'ny {bid}")
        else:
            with open(chemin, "wb") as f:
                f.write(fichier.content)
            fichiers.append(ext)
            print(f"  Voaray: {chemin}")
        time.sleep(2)

    rows.append({
        "id": bid,
        "lohateny": titre,
        "mpanoratra": auteurs,
        "mpamaky": mpamaky,
        "lohahevitra": "; ".join(sujets),
        "rohy": f"https://www.gutenberg.org/ebooks/{bid}",
        "fichiers": ", ".join(fichiers),
        "commentaire": commentaire,
    })
    time.sleep(2)

df = pd.DataFrame(rows, columns=COLONNES)
df.to_csv("tantara_malaza.csv", index=False)
print(f"Voatahiry: {len(df)} tantara")

if df.empty:
    print("TSY NISY BOKY NAHAZOINA: jereo ny hafatra etsy ambony.")
    sys.exit(1)
