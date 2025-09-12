# 🎮 Guide d'Intégration Discord VerseLink

## 📋 Vue d'ensemble

L'intégration Discord VerseLink offre une synchronisation bidirectionnelle complète entre votre plateforme VerseLink et vos serveurs Discord. Cette implémentation suit les priorités définies : **A-D-E-B-C**.

## ✨ Fonctionnalités Implémentées

### 🟢 PRIORITÉ A : Événements Discord Programmés (Guild Scheduled Events)
- ✅ Création automatique d'événements Discord lors de la création d'événements VerseLink
- ✅ Synchronisation des modifications (titre, description, date, etc.)
- ✅ Gestion des états (planifié, actif, terminé, annulé)
- ✅ Synchronisation des participants entre Discord et VerseLink

### 🟢 PRIORITÉ D : Réactions/Boutons pour Inscriptions
- ✅ Messages interactifs avec boutons d'inscription/désinscription
- ✅ Sélection de rôles via menus déroulants
- ✅ Affichage des participants en temps réel
- ✅ Synchronisation automatique des inscriptions Discord → VerseLink

### 🟢 PRIORITÉ E : Synchronisation Bidirectionnelle Complète
- ✅ Système de webhooks pour les événements Discord
- ✅ Jobs asynchrones pour traitement fiable
- ✅ Gestion des erreurs et retry automatique
- ✅ Logs complets des interactions

### 🟡 PRIORITÉ B : Gestion Automatique des Rôles
- ✅ Structure de base pour mapping rôles Discord ↔ VerseLink
- ✅ Attribution automatique lors d'inscriptions
- 🔄 **À configurer** : Role menus interactifs

### 🟡 PRIORITÉ C : Création/Gestion Automatique des Salons
- ✅ Structure de base pour création de salons par événement
- ✅ Système de permissions configurables
- 🔄 **À configurer** : Archivage automatique

## 🔧 Configuration Requise

### 1. Variables d'Environnement

Ajoutez ces variables à `/app/backend/.env` :

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=votre-token-de-bot-discord
DISCORD_BOT_WEBHOOK_SECRET=votre-secret-webhook
DISCORD_BOT_API_URL=http://localhost:3001
DISCORD_BOT_API_TOKEN=votre-token-api-bot

# Discord OAuth2 (si pas déjà configuré)
DISCORD_CLIENT_ID=votre-client-id-discord
DISCORD_CLIENT_SECRET=votre-client-secret-discord
```

### 2. Permissions Discord Bot

Votre bot Discord doit avoir ces permissions :
- `bot` (scope)
- `applications.commands` (scope)
- `guilds` (scope)
- `guilds.members.read` (scope)
- **Permissions** :
  - Gérer les événements programmés
  - Envoyer des messages
  - Utiliser les commandes slash
  - Gérer les rôles
  - Gérer les salons
  - Ajouter des réactions

## 🚀 Utilisation

### Configuration d'un Serveur Discord

1. **Inviter le bot** sur votre serveur Discord
2. **Associer le serveur** à une organisation VerseLink :
   ```bash
   POST /api/v1/discord/guilds
   {
     "guild_id": "123456789",
     "guild_name": "Mon Serveur",
     "owner_id": "987654321",
     "org_id": "organisation-id",
     "announcement_channel_id": "canal-annonces-id",
     "event_channel_id": "canal-evenements-id"
   }
   ```

### Création d'Événements avec Intégration Discord

Les événements créés sur VerseLink sont automatiquement :
1. **Créés sur Discord** comme événements programmés
2. **Synchronisés** en temps réel lors des modifications
3. **Dotés de messages interactifs** pour les inscriptions

### Gestion des Inscriptions via Discord

Les utilisateurs peuvent :
1. **S'inscrire** directement via les boutons Discord
2. **Choisir leur rôle** via les menus déroulants
3. **Voir la liste** des participants
4. **Se désinscrire** facilement

## 🔗 API Endpoints

### Événements Discord
```bash
# Créer des événements Discord pour un événement VerseLink
POST /api/v1/discord/events/events/create/{event_id}

# Mettre à jour les événements Discord
PUT /api/v1/discord/events/events/update/{event_id}

# Supprimer les événements Discord
DELETE /api/v1/discord/events/events/delete/{event_id}

# Créer un message interactif d'inscription
POST /api/v1/discord/events/events/{event_id}/signup-message

# Synchroniser les participants
POST /api/v1/discord/events/events/{event_id}/sync-attendees
```

### Gestion Automatique
```bash
# Auto-gestion du cycle de vie des événements
POST /api/v1/discord/events/auto-manage/{event_id}?action=created
POST /api/v1/discord/events/auto-manage/{event_id}?action=updated
POST /api/v1/discord/events/auto-manage/{event_id}?action=cancelled
```

### Interactions Discord
```bash
# Handler pour les interactions Discord (boutons, menus)
POST /api/v1/discord/events/interactions
```

## 📊 Monitoring et Statistiques

### Health Checks
```bash
# Vérifier l'état de l'intégration Discord
GET /api/v1/discord/events/health

# Statistiques détaillées
GET /api/v1/discord/events/stats/events
```

### Logs et Jobs
```bash
# Lister les jobs Discord
GET /api/v1/discord/jobs

# Déclencher le traitement manuel des jobs
POST /api/v1/discord/jobs/process
```

## 🛠️ Architecture Technique

### Services Principaux
- **DiscordEventsService** : Gestion des événements programmés
- **DiscordService** : Service principal avec jobs et webhooks
- **EventService** : Service VerseLink étendu avec hooks Discord

### Modèles de Données
- **DiscordEvent** : Événements Discord programmés
- **InteractiveMessage** : Messages avec boutons/menus
- **DiscordRoleMapping** : Mapping des rôles
- **DiscordChannelMapping** : Mapping des salons
- **DiscordJob** : Jobs asynchrones

### Base de Données
Collections MongoDB automatiquement créées :
- `discord_events`
- `interactive_messages`  
- `discord_role_mappings`
- `discord_channel_mappings`
- `discord_jobs`

## 🔄 Workflow Complet

1. **Création d'événement sur VerseLink**
   → Déclenche automatiquement la création Discord

2. **Événement Discord créé**
   → Message interactif posté automatiquement

3. **Utilisateur clique sur "S'inscrire"**
   → Inscription synchronisée sur VerseLink

4. **Modification sur VerseLink**
   → Mise à jour automatique sur Discord

5. **Événement terminé**
   → Nettoyage automatique des salons (optionnel)

## 🧪 Tests et Validation

### Test d'Intégration
```bash
cd /app && python test_discord_integration.py
```

### Tests Manuels
1. Créer un événement sur VerseLink
2. Vérifier la création sur Discord
3. Tester les inscriptions via Discord
4. Modifier l'événement sur VerseLink
5. Vérifier la synchronisation

## 📈 Prochaines Améliorations

### Fonctionnalités Avancées
- [ ] Role menus interactifs complets
- [ ] Création automatique de salons vocaux
- [ ] Notifications DM personnalisées
- [ ] Intégration avec les threads Discord
- [ ] Analytics avancés des interactions

### Optimisations
- [ ] Cache des données Discord
- [ ] Rate limiting intelligent
- [ ] Retry policies configurables
- [ ] Monitoring proactif

## 🆘 Dépannage

### Problèmes Courants

**Événements non créés sur Discord :**
- Vérifier le token du bot
- Vérifier les permissions du bot
- Consulter les logs des jobs : `GET /api/v1/discord/jobs?status=failed`

**Inscriptions non synchronisées :**
- Vérifier la configuration des webhooks
- Tester l'endpoint interactions : `POST /api/v1/discord/events/interactions`

**Messages interactifs non fonctionnels :**
- Vérifier l'ID du canal configuré
- Tester la santé du service : `GET /api/v1/discord/events/health`

### Logs Utiles
```bash
# Logs du scheduler Discord
tail -f /var/log/supervisor/backend.err.log | grep "Discord"

# Logs des jobs
GET /api/v1/discord/jobs?limit=10

# Statistiques en temps réel
GET /api/v1/discord/stats
```

---

## 🎉 Conclusion

L'intégration Discord VerseLink est maintenant **fonctionnelle et prête pour la production**. Toutes les priorités principales (A, D, E) sont implémentées avec une base solide pour les priorités B et C.

La solution offre une expérience utilisateur fluide avec une synchronisation bidirectionnelle complète entre VerseLink et Discord.

**🚀 Prêt à déployer et à configurer avec vos clés Discord !**