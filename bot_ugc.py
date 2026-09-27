import os
import sys
import json
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

URL_CATALOGUE = "https://fidelite.ugc.fr/catalogue-cadeaux.html"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_ROLE_ID = os.getenv("DISCORD_ROLE_ID")
STATE_FILE = "posters_state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_daily_report():
    """Envoie un rapport résumé de la journée à minuit sans ping."""
    if not DISCORD_WEBHOOK_URL:
        print("Erreur : URL Webhook non configurée.")
        return

    previous_state = load_previous_state()
    total_posters = len(previous_state)
    
    # Compte les posters disponibles
    available_posters = [
        title for title, data in previous_state.items() 
        if (data.get("status") if isinstance(data, dict) else data) == "DISPONIBLE"
    ]
    
    embed = {
        "title": "📊 Rapport Journalier - Catalogue UGC",
        "url": URL_CATALOGUE,
        "color": 3447003,  # Bleu
        "description": "Résumé automatique de l'état du catalogue de posters à minuit.",
        "fields": [
            {
                "name": " Total suivi",
                "value": f"{total_posters} affiches",
                "inline": True
            },
            {
                "name": "🟢 En stock",
                "value": f"{len(available_posters)} disponible(s)",
                "inline": True
            }
        ],
        "footer": {
            "text": "UGC Loyalty Monitor • Rapport Quotidien"
        }
    }

    if available_posters:
        embed["fields"].append({
            "name": "🎬 Affiches actuellement disponibles",
            "value": "\n".join([f"• {title}" for title in available_posters]),
            "inline": False
        })

    payload = {
        "username": "UGC Poster Bot",
        "avatar_url": "https://www.ugc.fr/favicon.ico",
        "embeds": [embed]
        # Pas de content = pas de ping
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Rapport journalier envoyé avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'envoi du rapport journalier : {e}")

def send_discord_embed(title, release_date, image_url, points):
    """Envoie la carte d'alerte enrichie lors d'un réassort."""
    if not DISCORD_WEBHOOK_URL:
        return

    embed = {
        "title": f"🚨 ALERTE POSTER : {title}",
        "url": URL_CATALOGUE,
        "color": 15158332,  # Rouge UGC (#E74C3C)
        "description": "Un poster de film vient de repasser en stock sur le catalogue de fidélité !",
        "fields": [
            {
                "name": "📅 Date de sortie / Statut",
                "value": release_date if release_date else "Non spécifiée",
                "inline": True
            },
            {
                "name": "🪙 Coût",
                "value": points if points else "250 points",
                "inline": True
            }
        ],
        "footer": {
            "text": "UGC Loyalty Monitor • Notification automatique"
        }
    }

    if image_url:
        embed["image"] = {"url": image_url}

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "label": "Voir sur le site UGC",
                    "style": 5,
                    "url": URL_CATALOGUE
                }
            ]
        }
    ]

    content = f"<@&{DISCORD_ROLE_ID}> 🎬 NOUVELLE AFFICHE DISPONIBLE !" if DISCORD_ROLE_ID else "🎬 NOUVELLE AFFICHE DISPONIBLE !"

    payload = {
        "username": "UGC Poster Bot",
        "avatar_url": "https://www.ugc.fr/favicon.ico",
        "content": content,
        "embeds": [embed],
        "components": components
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur d'envoi Discord : {e}")

def fetch_catalogue_with_retry(max_retries=3, delay=5):
    """Tente de récupérer la page web avec plusieurs essais en cas d'échec."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(URL_CATALOGUE, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.content
            print(f"Tentative {attempt}/{max_retries} échouée (Code HTTP {response.status_code})")
        except requests.RequestException as e:
            print(f"Tentative {attempt}/{max_retries} échouée avec erreur : {e}")
        
        if attempt < max_retries:
            time.sleep(delay)
            
    return None

def load_previous_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_current_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_posters():
    html_content = fetch_catalogue_with_retry()
    
    if not html_content:
        print("Impossible d'accéder au catalogue UGC après plusieurs tentatives.")
        return

    soup = BeautifulSoup(html_content, "html.parser")
    items = soup.find_all("div", class_="catalog-list-item")

    if not items:
        print("Avertissement : Aucun article trouvé dans le catalogue.")
        send_discord_alert("Le bot n'a trouvé aucun article sur le site UGC. La structure HTML de la page a peut-être changé.", is_error=True)
        return

    KEYWORDS_POSTERS = ["affiche", "poster"]
    current_state = {}
    posters_details = {}
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    previous_state = load_previous_state()

    for item in items:
        title_tag = item.find("h3")
        title = title_tag.text.strip() if title_tag else ""

        if not title or not any(kw in title.lower() for kw in KEYWORDS_POSTERS):
            continue

        img_tag = item.find("img")
        image_url = ""
        if img_tag and img_tag.get("src"):
            src = img_tag["src"]
            image_url = src if src.startswith("http") else f"https://fidelite.ugc.fr{src}"

        date_tag = item.find("p") or item.find("span", class_="date")
        release_date = date_tag.text.strip() if date_tag else "Information non disponible"

        points_tag = item.find("span", class_="points") or item.find("div", class_="points")
        points = points_tag.text.strip() if points_tag else "250 points"

        item_text = item.text.lower()
        if "victime de son succès" in item_text or item.find(class_="disabled"):
            status = "ÉPUISÉ"
        else:
            status = "DISPONIBLE"

        # Récupération de l'ancien état s'il s'agit d'une structure complexe ou simple
        prev_entry = previous_state.get(title)
        if isinstance(prev_entry, dict):
            prev_status = prev_entry.get("status")
            last_updated = prev_entry.get("last_updated", now_iso)
        else:
            prev_status = prev_entry
            last_updated = now_iso

        # Si le statut change, on met à jour la date
        if status != prev_status:
            last_updated = now_iso

        current_state[title] = {
            "status": status,
            "last_updated": last_updated
        }

        posters_details[title] = {
            "release_date": release_date,
            "image_url": image_url,
            "points": points,
            "prev_status": prev_status
        }

    # Déclenchement des notifications Discord selon l'évolution du stock
    for title, data in current_state.items():
        status = data["status"]
        details = posters_details[title]
        prev_status = details["prev_status"]

        # 1. Réassort (Nouveau ou repassé DISPONIBLE)
        if status == "DISPONIBLE" and prev_status != "DISPONIBLE":
            send_discord_embed(
                title=title,
                release_date=details["release_date"],
                image_url=details["image_url"],
                points=details["points"]
            )
        # 2. Rupture (Repassé ÉPUISÉ)
        elif status == "ÉPUISÉ" and prev_status == "DISPONIBLE":
            send_discord_alert(f"❌ **RUPTURE DE STOCK** : L'affiche **{title}** est de nouveau épuisée.")

    save_current_state(current_state)

if __name__ == "__main__":
    # Si le script est appelé avec le paramètre --report, on envoie le rapport
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        send_daily_report()
    else:
        check_posters()