# 🎬 UGC Poster Monitor

Un bot automatisé permettant de surveiller en temps réel le catalogue de cadeaux du programme de fidélité UGC. Il envoie une notification immédiate sur Discord dès qu'un poster de film repasse en stock.

## 🚀 Fonctionnalités
- **Scraping ciblé** : Analyse du catalogue UGC pour extraire uniquement les affiches de films.
- **Détection d'état** : Identification précise de la disponibilité (gestion des statuts *Victime de son succès*).
- **Notifications instantanées** : Envoi d'alertes enrichies sur Discord via Webhook.
- **Exécution 100 % Cloud & Automatique** : Tourne toutes les 15 minutes via GitHub Actions.
- **Gestion d'état** : Historisation de l'état du stock dans un fichier JSON pour éviter le spam.

## 🛠️ Stack Technique
- **Langage** : Python 3.10+
- **Parsing HTML** : BeautifulSoup4 & Requests
- **CI/CD & Cloud** : GitHub Actions
- **Alertes** : Discord Webhook API

## ⚙️ Configuration

### Préréquis
1. Créer un Webhook sur ton serveur Discord (*Paramètres du salon -> Intégrations -> Webhooks*).
2. Ajouter le Webhook à ton dépôt GitHub :
   - Aller dans **Settings** > **Secrets and variables** > **Actions**.
   - Cliquer sur **New repository secret**.
   - Nom : `DISCORD_WEBHOOK_URL`
   - Valeur : URL de ton webhook Discord.

---
*Projet développé à des fins d'automatisation personnelle.*
