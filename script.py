import csv
import io
import os
import time
import requests

CATALOGUE = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
DOSSIER = "livres"
FOTOANA_MAX = 5 * 3600        # 5 ora, mba hahatongavan'ny workflow ao amin'ny fetra 6 ora
HEADERS = {"User-Agent": "TantaraBot/1.0 (fampiasana manokana)"}
FICHIER_VOARAY = os.path.join(DOSSIER, "voaray.txt")
os.makedirs(DOSSIER, exist_ok=True)
start = time.monotonic()


def telecharger(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
        if r.status_code == 200 and r.content:
            return r.content
        print(f"  Status {r.status_code}: {url}")
    except requests.RequestException as e:
        print(f"  Hadisoana: {e}")
    return None


# 1. Katalogy
r = requests.get(CATALOGUE, headers=HEADERS, timeout=180)
r.raise_for_status()
catalogue = csv.DictReader(io.StringIO(r.content.decode("utf-8-sig")))
frantsay = [
    row for row in catalogue
    if row.get("Language") == "French" and row.get("Type") == "Text"
]
print(f"Boky frantsay rehetra: {len(frantsay)}")

# 2. Boky efa voaray (avy amin'ny fandehanana teo aloha)
voaray = set()
if os.path.exists(FICHIER_VOARAY):
    with open(FICHIER_VOARAY, encoding="utf-8") as f:
        voaray = {ligne.strip() for ligne in f if ligne.strip()}

# 3. Fampidinana, mijanona rehefa tonga ny fotoana
metadata = []
for row in frantsay:
    if time.monotonic() - start > FOTOANA_MAX:
        print("Fotoana tanteraka: mijanona eto, mitohy amin'ny fandehanana manaraka.")
        break

    bid = row["Text#"]
    if bid in voaray:
        continue

    titre = row.get("Title", "")
    print(f"Boky {bid}: {titre}")
    metadata.append({
        "id": bid,
        "lohateny": titre,
        "mpanoratra": row.get("Authors", ""),
        "rohy": f"https://www.gutenberg.org/ebooks/{bid}",
    })

    voaray_ok = False
    for ext, url in {
        "txt": f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.txt",
        "epub": f"https://www.gutenberg.org/ebooks/{bid}.epub.noimages",
    }.items():
        contenu = telecharger(url)
        if contenu:
            chemin = os.path.join(DOSSIER, f"{bid}.{ext}")
            with open(chemin, "wb") as f:
                f.write(contenu)
            voaray_ok = True
            print(f"  Voaray: {chemin} ({len(contenu) // 1024} KB)")
        else:
            print(f"  Tsy nahazo {ext}")
        time.sleep(2)

    if voaray_ok:
        voaray.add(bid)
        with open(FICHIER_VOARAY, "a", encoding="utf-8") as f:
            f.write(bid + "\n")
    time.sleep(2)

# 4. Lisitra metadata (fanampiana raha efa misy)
chemin_csv = os.path.join(DOSSIER, "boky.csv")
mode_csv = "a" if os.path.exists(chemin_csv) else "w"
with open(chemin_csv, mode_csv, newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "lohateny", "mpanoratra", "rohy"])
    if mode_csv == "w":
        writer.writeheader()
    writer.writerows(metadata)

print(f"Voatahiry vaovao: {len(metadata)} boky | Efa voaray hatramin'izao: {len(voaray)}")
