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

def send_discord_notification(message):
    if not DISCORD_WEBHOOK_URL:
        print("Erreur : URL Webhook non configurée.")
        return
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
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

    # Mots-clés pour ne garder QUE les cartes d'affiches
    KEYWORDS_POSTERS = ["affiche", "poster"]

    current_state = {}

    for item in items:
        # Récupération du titre
        title_tag = item.find("h3")
        title = title_tag.text.strip() if title_tag else ""

        if not title:
            continue

        title_lower = title.lower()

        # Filtrage : On ne garde que les articles parlant d'affiches/posters
        if not any(kw in title_lower for kw in KEYWORDS_POSTERS):
            continue

        # Récupération de tout le texte dans le bloc de la carte
        item_text = item.text.lower()

        # Analyse de la disponibilité :
        # Si la carte contient "victime de son succès" ou la classe disabled
        if "victime de son succès" in item_text or item.find(class_="disabled"):
            current_state[title] = "ÉPUISÉ"
        else:
            current_state[title] = "DISPONIBLE"

    previous_state = load_previous_state()

    # Analyse des changements
    for title, status in current_state.items():
        prev_status = previous_state.get(title)

        # Poster de nouveau disponible
        if status == "DISPONIBLE" and prev_status != "DISPONIBLE":
            msg = f"🚨 **ALERTE POSTER UGC !**\nLe poster **{title}** est maintenant **DISPONIBLE** !\n👉 {URL_CATALOGUE}"
            send_discord_notification(msg)

        # Nouveau poster ajouté au catalogue directement disponible
        elif prev_status is None and status == "DISPONIBLE":
            msg = f"✨ **NOUVEAU POSTER !**\n**{title}** est disponible !\n👉 {URL_CATALOGUE}"
            send_discord_notification(msg)

    # Sauvegarde
    save_current_state(current_state)

if __name__ == "__main__":
    check_posters()