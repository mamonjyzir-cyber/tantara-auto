import os
import re
import time
import requests
import pandas as pd

URL = "https://gutendex.com/books/?topic=fiction&sort=popular&languages=en"
MAX_TANTARA = 20
DOSSIER = "livres"
HEADERS = {"User-Agent": "TantaraBot/1.0 (fampiasana manokana)"}

FORMATS = {
    "epub": "application/epub+zip",
    "pdf": "application/pdf",
    "txt": "text/plain",
}

COLONNES = ["lohateny", "mpanoratra", "mpamaky", "lohahevitra", "rohy", "fichiers", "commentaire"]

os.makedirs(DOSSIER, exist_ok=True)


def nom_fichier(texte):
    return re.sub(r"[^\w\-]+", "_", texte)[:80].strip("_") or "boky"


def telecharger(url, chemin):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(chemin, "wb") as f:
        f.write(r.content)


def lire_katalogy(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Tsy nahomby ny famakiana katalogy: {url} ({e})")
        return None


rows = []
url = URL

while url and len(rows) < MAX_TANTARA:
    data = lire_katalogy(url)
    if not data:
        break

    for b in data.get("results", []):
        if len(rows) >= MAX_TANTARA:
            break
        try:
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
                    continue
                chemin = os.path.join(DOSSIER, f"{b['id']}_{nom_fichier(b.get('title', ''))}.{ext}")
                try:
                    telecharger(lien, chemin)
                    fichiers.append(ext)
                    print(f"Voaray: {chemin}")
                except Exception as e:
                    print(f"Tsy nahomby: {b.get('title')} ({ext}): {e}")
                time.sleep(1)

            rows.append({
                "lohateny": b.get("title", ""),
                "mpanoratra": auteurs,
                "mpamaky": mpamaky,
                "lohahevitra": "; ".join(sujets),
                "rohy": f"https://www.gutenberg.org/ebooks/{b['id']}",
                "fichiers": ", ".join(fichiers),
                "commentaire": commentaire,
            })
        except Exception as e:
            print(f"Tsy nahomby ny boky iray: {e}")

    url = data.get("next")
    time.sleep(1)

df = pd.DataFrame(rows, columns=COLONNES)
if not df.empty:
    df = df.sort_values("mpamaky", ascending=False)
df.to_csv("tantara_malaza.csv", index=False)

print(f"Voatahiry: {len(df)} tantara")
