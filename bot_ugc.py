import os
import json
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
URL_CATALOGUE = "https://fidelite.ugc.fr/catalogue-cadeaux.html" # Ajuste si besoin
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1553769501248716873/VlHSNm-gv7XaoWrGCKnM3YhJaRAJQpptxminBDbkSENMJi3Pq8rQTuK-FYqYAv7D74oq"

STATE_FILE = "posters_state.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_discord_notification(message):
    """Envoie un message sur Discord via Webhook"""
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Erreur d'envoi Discord : {e}")

def load_previous_state():
    """Charge le dernier état connu des posters"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_current_state(state):
    """Sauvegarde l'état actuel"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_posters():
    response = requests.get(URL_CATALOGUE, headers=HEADERS)
    if response.status_code != 200:
        print(f"Erreur lors du chargement de la page : {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.find_all("div", class_="catalog-list-item")

    current_state = {}
    
    for item in items:
        # Récupération du titre
        title_tag = item.find("h3")
        title = title_tag.text.strip() if title_tag else "Film inconnu"
        
        # Récupération du bouton
        button = item.find("a", class_="cta")
        
        if button:
            is_disabled = "disabled" in button.get("class", [])
            button_text = button.text.strip()
            
            # Détermination de la disponibilité
            if is_disabled or "victime de son succès" in button_text.lower():
                current_state[title] = "ÉPUISÉ"
            else:
                current_state[title] = "DISPONIBLE"

    previous_state = load_previous_state()

    # Analyse des changements
    for title, status in current_state.items():
        prev_status = previous_state.get(title)

        # Cas 1 : Le poster est disponible alors qu'il ne l'était pas
        if status == "DISPONIBLE" and prev_status != "DISPONIBLE":
            msg = f"🚨 **ALERTE POSTER UGC !**\nLe poster **{title}** est maintenant **DISPONIBLE** !\n👉 {URL_CATALOGUE}"
            print(msg)
            send_discord_notification(msg)
        
        # Cas 2 : Nouveau poster ajouté au catalogue
        elif prev_status is None:
            if status == "DISPONIBLE":
                msg = f"✨ **NOUVEAU POSTER !**\n**{title}** vient d'être ajouté et est **DISPONIBLE** !\n👉 {URL_CATALOGUE}"
                send_discord_notification(msg)

    # Mise à jour de la sauvegarde
    save_current_state(current_state)

if __name__ == "__main__":
    check_posters()