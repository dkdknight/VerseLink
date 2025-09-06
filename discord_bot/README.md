# 🤖 VerseLink Discord Bot

Bot Discord officiel pour la plateforme VerseLink Star Citizen.

## 🚀 Installation et Configuration

### 1. Prérequis
- Python 3.8+
- Discord Bot Token
- Token d'API VerseLink (admin)

### 2. Configuration

Copiez le fichier de configuration :
```bash
cp .env.example .env
```

Modifiez le fichier `.env` avec vos tokens :
```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# VerseLink API Configuration
VERSELINK_API_BASE=http://89.88.206.99:8001/api/v1
VERSELINK_API_TOKEN=your_verselink_api_token_here

# Bot Configuration
BOT_PREFIX=!vl
DEBUG_MODE=true
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 3. Installation des Dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancement

#### Méthode Simple (Recommandée)
```bash
./start_bot.sh
```

#### Méthode Manuelle
```bash
python3 bot.py
```

## 🔑 Obtenir les Tokens

### Discord Bot Token

1. Allez sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Créez une nouvelle application
3. Onglet "Bot" → "Add Bot"
4. Copiez le token
5. **Permissions requises** :
   - Send Messages
   - Send Messages in Threads
   - Embed Links
   - Attach Files  
   - Read Message History
   - Use Slash Commands
   - Manage Messages
   - Add Reactions

### VerseLink API Token

1. Connectez-vous sur [VerseLink](http://89.88.206.99:3000) avec un compte admin
2. Ouvrez Developer Tools (F12)
3. Application/Storage → Local Storage
4. Copiez la valeur de `auth_token`

## 📋 Commandes Disponibles

### Commandes de Base
- `/help` - Afficher l'aide
- `/status` - Statut du système VerseLink
- `/events` - Lister les événements
- `/tournaments` - Lister les tournois
- `/event-info <id>` - Détails d'un événement
- `/tournament-bracket <id>` - Bracket d'un tournoi

### Commandes Admin (Permissions Manage Guild)
- `/setup` - Configurer ce serveur avec VerseLink
- `/config` - Voir la configuration du serveur
- `/set-channel <type> <channel>` - Définir les canaux (events, tournaments, announcements)
- `/toggle <feature> <enabled>` - Activer/désactiver des fonctionnalités
- `/sync-message <message_id>` - Synchroniser un message entre serveurs
- `/remind <message> <delay_hours>` - Programmer un rappel

### Commandes Utilisateur
- `/join-event <id>` - S'inscrire à un événement
- `/join-tournament <id>` - S'inscrire à un tournoi
- `/leave-event <id>` - Se désinscrire d'un événement
- `/leave-tournament <id>` - Se désinscrire d'un tournoi
- `/profile` - Afficher votre profil VerseLink
- `/link-account` - Lier votre compte Discord à VerseLink

### Commandes Techniques (Admins Bot)
- `/bot-info` - Informations techniques du bot
- `/reload-config` - Recharger la configuration

## 🔧 Fonctionnalités

### 🔄 Annonces Automatiques
- Nouveaux événements
- Nouveaux tournois  
- Résultats de matchs
- Rappels automatiques

### 🌐 Synchronisation Multi-Serveurs
- Messages synchronisés entre serveurs
- Annonces centralisées
- Configuration par serveur

### ⏰ Système de Rappels
- Rappels d'événements (24h, 1h, 15min)
- Rappels personnalisés
- Gestion par serveur

### 🛡️ Auto-Modération
- Détection de contenu inapproprié
- Actions automatiques configurables
- Intégration avec le système VerseLink

### 📊 Monitoring
- Santé du système
- Statistiques d'usage
- Logs détaillés

## 🏗️ Architecture

```
discord_bot/
├── bot.py              # Bot principal
├── config.py           # Configuration
├── verselink_api.py    # Client API VerseLink
├── commands.py         # Commandes principales
├── admin_commands.py   # Commandes admin
├── utils.py            # Utilitaires
├── requirements.txt    # Dépendances
├── start_bot.sh       # Script de lancement
├── .env.example       # Configuration exemple
└── README.md          # Cette documentation
```

## 🔗 Intégration VerseLink

Le bot communique avec l'API VerseLink via les endpoints :

- `/discord/bot/verify` - Vérification du bot
- `/discord/bot/guild/{guild_id}/*` - Gestion des serveurs
- `/discord/announce/*` - Système d'annonces
- `/discord/sync/*` - Synchronisation des messages
- `/discord/reminders/*` - Gestion des rappels
- `/discord/jobs/*` - Traitement des tâches
- `/discord/health` - Santé du système
- `/events/*` - Événements
- `/tournaments/*` - Tournois

## 🐛 Dépannage

### Bot ne démarre pas
1. Vérifiez le token Discord
2. Vérifiez la connexion API VerseLink
3. Consultez les logs : `tail -f bot.log`

### Commandes ne fonctionnent pas
1. Vérifiez les permissions du bot sur Discord
2. Utilisez `/setup` pour configurer le serveur
3. Vérifiez que l'API VerseLink est accessible

### API Errors
1. Vérifiez le token API VerseLink
2. Vérifiez que l'URL API est correcte
3. Testez manuellement : `curl -H "Authorization: Bearer TOKEN" API_URL/discord/health`

## 📞 Support

- **Logs** : Consultez `bot.log` pour les erreurs détaillées
- **API VerseLink** : [http://89.88.206.99:3000](http://89.88.206.99:3000)
- **Documentation API** : [http://89.88.206.99:8001/docs](http://89.88.206.99:8001/docs)

## 🔄 Mise à Jour

Pour mettre à jour le bot :
1. Arrêtez le bot (Ctrl+C)
2. `git pull` (si utilisant git)
3. `pip install -r requirements.txt`
4. `./start_bot.sh`

## 📝 Logs

Les logs sont stockés dans :
- `bot.log` - Logs complets du bot
- Console - Logs en temps réel

Niveaux de logs configurables dans `.env` :
- `DEBUG` - Très détaillé
- `INFO` - Normal (recommandé)
- `WARNING` - Warnings seulement
- `ERROR` - Erreurs seulement