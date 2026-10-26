import os
import re
import time
import requests
import pandas as pd

URL = "https://gutendex.com/books/?topic=fiction&sort=popular&languages=en"
MAX_TANTARA = 20
DOSSIER = "livres"
HEADERS = {"User-Agent": "TantaraBot/1.0 (fampiasana manokana)"}

# Karazana file tadiavina: extension -> MIME type ao amin'ny Gutendex
FORMATS = {
    "epub": "application/epub+zip",
    "pdf": "application/pdf",
    "txt": "text/plain",
}

os.makedirs(DOSSIER, exist_ok=True)


def nom_fichier(texte):
    return re.sub(r"[^\w\-]+", "_", texte)[:80].strip("_")


def telecharger(url, chemin):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(chemin, "wb") as f:
        f.write(r.content)


rows = []
url = URL

while url and len(rows) < MAX_TANTARA:
    data = requests.get(url, headers=HEADERS, timeout=20).json()

    for b in data["results"]:
        if len(rows) >= MAX_TANTARA:
            break

        auteurs = ", ".join(a["name"] for a in b["authors"]) or "Tsy fantatra"
        sujets = b.get("subjects", [])[:2]
        mpamaky = b.get("download_count", 0)

        commentaire = f"Malaza amin'ny mpamaky {mpamaky:,} ; mpanoratra: {auteurs}"
        if sujets:
            commentaire += f" ; lohahevitra: {'; '.join(sujets)}"

        # Mampidina ny file (EPUB, PDF, TXT) raha misy
        fichiers = []
        for ext, mime in FORMATS.items():
            lien = next((u for k, u in b["formats"].items() if k.startswith(mime)), None)
            if not lien:
                continue
            chemin = os.path.join(DOSSIER, f"{b['id']}_{nom_fichier(b['title'])}.{ext}")
            try:
                telecharger(lien, chemin)
                fichiers.append(ext)
                print(f"Voaray: {chemin}")
            except requests.RequestException as e:
                print(f"Tsy nahomby: {b['title']} ({ext}): {e}")
            time.sleep(1)

        rows.append({
            "lohateny": b["title"],
            "mpanoratra": auteurs,
            "mpamaky": mpamaky,
            "lohahevitra": "; ".join(sujets),
            "rohy": f"https://www.gutenberg.org/ebooks/{b['id']}",
            "fichiers": ", ".join(fichiers),
            "commentaire": commentaire,
        })

    url = data.get("next")
    time.sleep(1)

df = pd.DataFrame(rows).sort_values("mpamaky", ascending=False)
df.to_csv("tantara_malaza.csv", index=False)

print(f"Voatahiry: {len(df)} tantara")
