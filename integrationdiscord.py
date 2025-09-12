import requests

# URL de ton backend VerseLink
url = "http://knight-hd.fr:8001/api/v1/discord/guilds"
# ou "http://knight-hd.fr:3000/api/v1/discord/guilds" si ton backend est bien exposé dessus

# Ton token admin (vérifie dans ton .env ou via ton endpoint /auth/login)
headers = {
    "Authorization": "Bearer UnTresLongSecretAleatoire123",
    "Content-Type": "application/json"
}

# Les données à envoyer
data = {
    "guild_id": "1412862353657172072",          # ID du serveur Discord
    "guild_name": "Team-HD",                    # Nom du serveur
    "owner_id": "383961549343162379",           # ⚠️ ID Discord du propriétaire (pas un UUID)
    "org_id": "8e27b256-bc7f-493d-b380-3ccb9a709c11",  # ID de ton org VerseLink
    "announcement_channel_id": "1412862354642698382",  # ID canal annonces
    "event_channel_id": "1412862413069619210"          # ID canal events
}

# Envoi de la requête
response = requests.post(url, headers=headers, json=data)

# Affiche le résultat
print("Status:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Raw response:", response.text)