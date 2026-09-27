import os
import json
import requests
from bs4 import BeautifulSoup

URL_CATALOGUE = "https://fidelite.ugc.fr/catalogue-cadeaux.html"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "posters_state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_discord_embed(title, release_date, image_url, points):
    if not DISCORD_WEBHOOK_URL:
        print("Erreur : URL Webhook non configurée.")
        return

    # Structure de la carte Embed Discord
    embed = {
        "title": f"🚨 ALERTE POSTER : {title}",
        "url": URL_CATALOGUE,
        "color": 15158332,  # Rouge UGC (Code Hex #E74C3C en entier)
        "description": "Un poster de film vient de repasser en stock sur le catalogue de fidélité !",
        "fields": [
            {
                "name": "📅 Date de sortie / Statut",
                "value": release_date if release_date else "Non spécifiée",
                "inline": True
            },
            {
                "name": "🪙 Cout",
                "value": points if points else "250 points",
                "inline": True
            }
        ],
        "image": {
            "url": image_url
        } if image_url else {},
        "footer": {
            "text": "UGC Loyalty Monitor • Notification automatique"
        }
    }

    payload = {
        "username": "UGC Poster Bot",
        "avatar_url": "https://www.ugc.fr/favicon.ico",
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur d'envoi Discord : {e}")

def load_previous_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_current_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_posters():
    response = requests.get(URL_CATALOGUE, headers=HEADERS)
    if response.status_code != 200:
        print(f"Erreur HTTP : {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.find_all("div", class_="catalog-list-item")

    KEYWORDS_POSTERS = ["affiche", "poster"]
    current_state = {}
    posters_details = {}

    for item in items:
        # 1. Titre du film
        title_tag = item.find("h3")
        title = title_tag.text.strip() if title_tag else ""

        if not title or not any(kw in title.lower() for kw in KEYWORDS_POSTERS):
            continue

        # 2. Extraction de l'image
        img_tag = item.find("img")
        image_url = ""
        if img_tag and img_tag.get("src"):
            src = img_tag["src"]
            image_url = src if src.startswith("http") else f"https://fidelite.ugc.fr{src}"

        # 3. Extraction de la date de sortie / sous-titre
        date_tag = item.find("p") or item.find("span", class_="date")
        release_date = date_tag.text.strip() if date_tag else "Information non disponible"

        # 4. Extraction du coût en points
        points_tag = item.find("span", class_="points") or item.find("div", class_="points")
        points = points_tag.text.strip() if points_tag else "250 points"

        # 5. Évaluation du statut
        item_text = item.text.lower()
        if "victime de son succès" in item_text or item.find(class_="disabled"):
            status = "ÉPUISÉ"
        else:
            status = "DISPONIBLE"

        current_state[title] = status
        posters_details[title] = {
            "release_date": release_date,
            "image_url": image_url,
            "points": points
        }

    previous_state = load_previous_state()

    # Déclenchement des alertes Embed
    for title, status in current_state.items():
        prev_status = previous_state.get(title)

        # Envoi si le poster repasse DISPONIBLE ou apparaît pour la première fois DISPONIBLE
        if status == "DISPONIBLE" and prev_status != "DISPONIBLE":
            details = posters_details[title]
            send_discord_embed(
                title=title,
                release_date=details["release_date"],
                image_url=details["image_url"],
                points=details["points"]
            )

    save_current_state(current_state)

if __name__ == "__main__":
    check_posters()