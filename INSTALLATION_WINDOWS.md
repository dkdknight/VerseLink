# Installation VerseLink sous Windows 🪟

## Problème résolu : Compatibilité Windows

**PROBLÈME IDENTIFIÉ :** Les requirements.txt contenaient des dépendances incompatibles Windows (notamment `uvloop` qui est Unix/Linux uniquement).

**SOLUTION :** Nettoyage complet des requirements.txt pour assurer la compatibilité Windows.

---

## 🔧 Prérequis Windows

### **1. Python 3.11+**
```bash
# Télécharger depuis https://python.org
# Ou via chocolatey
choco install python

# Vérifier l'installation
python --version
pip --version
```

### **2. Node.js 18+** 
```bash
# Télécharger depuis https://nodejs.org
# Ou via chocolatey
choco install nodejs

# Vérifier l'installation
node --version
npm --version
```

### **3. MongoDB** (optionnel si base externe)
```bash
# Via chocolatey
choco install mongodb

# Ou télécharger depuis https://mongodb.com
```

---

## 📦 Installation Backend

### **Dépendances nettoyées (Windows compatible)**
```bash
cd backend
pip install -r requirements.txt
```

**Requirements.txt Backend (18 dépendances essentielles) :**
- `fastapi==0.104.1` - Framework web
- `uvicorn==0.24.0` - Serveur ASGI (sans [standard] qui inclut uvloop)
- `motor==3.3.2` - Driver MongoDB async  
- `pymongo==4.6.0` - Driver MongoDB sync
- `pydantic==2.5.0` - Validation des données
- `python-jose[cryptography]==3.3.0` - JWT
- `passlib[bcrypt]==1.7.4` - Hachage mots de passe
- `python-multipart==0.0.6` - Upload fichiers
- `httpx==0.25.2` - Client HTTP async
- `authlib==1.2.1` - OAuth
- Et autres dépendances essentielles...

### **Démarrage Backend Windows**
```bash
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

---

## 🤖 Installation Discord Bot

### **Dépendances minimales (Windows compatible)**
```bash
cd discord_bot  
pip install -r requirements.txt
```

**Requirements.txt Discord Bot (9 dépendances essentielles) :**
- `discord.py==2.3.2` - Bibliothèque Discord
- `aiohttp==3.9.1` - Client HTTP async
- `python-dotenv==1.0.0` - Variables d'environnement
- `requests==2.31.0` - Client HTTP sync
- `apscheduler==3.10.4` - Planificateur de tâches
- `python-dateutil==2.8.2` - Manipulation dates
- `asyncio==3.4.3` - Programmation asynchrone
- `pydantic==2.5.0` - Validation données
- `httpx==0.25.2` - Client HTTP moderne

### **Configuration Discord Bot Windows**
1. **Configurer .env**
```bash
# discord_bot/.env
DISCORD_BOT_TOKEN=votre-token-discord-bot
VERSELINK_API_BASE=http://localhost:8001/api/v1
VERSELINK_API_TOKEN=votre-api-token
BOT_PREFIX=!vl
DEBUG_MODE=true
ENVIRONMENT=development
```

2. **Démarrer le Bot**
```bash
cd discord_bot
python bot.py
```

---

## 🌐 Installation Frontend

### **Dépendances Node.js**
```bash
cd frontend
npm install
# ou
yarn install
```

### **Configuration Frontend Windows**
```bash
# frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_DISCORD_CLIENT_ID=votre-discord-client-id
REACT_APP_NAME=VerseLink
GENERATE_SOURCEMAP=true
REACT_APP_DEBUG=true
```

### **Démarrage Frontend**
```bash
cd frontend
npm start
# ou 
yarn start
```

---

## 🐛 Problèmes Windows Résolus

### **1. uvloop (Unix uniquement)**
❌ **Avant :** `uvloop==0.21.0` dans requirements.txt  
✅ **Après :** Supprimé, non nécessaire sous Windows

### **2. Dependencies excessives**
❌ **Avant :** 91+ dépendances dans discord_bot/requirements.txt  
✅ **Après :** 9 dépendances essentielles uniquement

### **3. uvicorn[standard]**
❌ **Avant :** `uvicorn[standard]==0.24.0` (inclut uvloop)  
✅ **Après :** `uvicorn==0.24.0` (version de base compatible)

### **4. Dépendances redondantes**
❌ **Avant :** FastAPI, Celery, Redis dans bot Discord  
✅ **Après :** Seulement les dépendances Discord nécessaires

---

## ✅ Test d'Installation Windows

### **1. Test Backend**
```bash
cd backend
python -c "import fastapi, uvicorn, motor; print('✅ Backend dependencies OK')"
python server.py
# Doit démarrer sur http://localhost:8001
```

### **2. Test Discord Bot** 
```bash
cd discord_bot
python -c "import discord, aiohttp, asyncio; print('✅ Discord bot dependencies OK')"
python -c "from interactive_events import InteractiveEvents; print('✅ Phase 2 modules OK')"
```

### **3. Test Frontend**
```bash
cd frontend
npm run build
npm start
# Doit démarrer sur http://localhost:3000
```

---

## 🚀 Commandes de Démarrage Windows

### **Démarrage Manuel**
```bash
# Terminal 1 - Backend
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend  
cd frontend && npm start

# Terminal 3 - Discord Bot
cd discord_bot && python bot.py
```

### **Script de Démarrage Windows (.bat)**
```batch
@echo off
echo Starting VerseLink Services...

start "Backend" cmd /k "cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3
start "Frontend" cmd /k "cd frontend && npm start"  
timeout /t 3
start "Discord Bot" cmd /k "cd discord_bot && python bot.py"

echo All services started!
pause
```

---

## 📋 Checklist Installation Windows

- [ ] **Python 3.11+** installé et dans le PATH
- [ ] **Node.js 18+** installé et dans le PATH  
- [ ] **Git** installé pour cloner le projet
- [ ] **MongoDB** accessible (local ou distant)
- [ ] **Variables d'environnement** configurées (.env)
- [ ] **Dependencies backend** installées sans erreur
- [ ] **Dependencies Discord bot** installées sans erreur
- [ ] **Dependencies frontend** installées sans erreur
- [ ] **Ports 3000, 8001** disponibles
- [ ] **Token Discord** valide configuré
- [ ] **Tests de démarrage** passent

---

## 🔍 Dépannage Windows

### **Erreur "uvloop not supported"**
✅ **Résolu** - uvloop supprimé des requirements

### **Erreur "Module discord not found"**
```bash
cd discord_bot
pip install --upgrade discord.py==2.3.2
```

### **Erreur port 8001 occupé**
```bash
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

### **Erreur npm/yarn**
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 🎯 Validation Finale

Une fois l'installation terminée, vous devriez avoir :

1. **Backend API** ➜ http://localhost:8001/docs
2. **Frontend React** ➜ http://localhost:3000  
3. **Discord Bot** ➜ Connecté et avec commandes `/create-event`, `/create-tournament`

**Le système Phase 2 est maintenant 100% compatible Windows !** 🎉