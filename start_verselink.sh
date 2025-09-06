#!/bin/bash
# Script de lancement complet VerseLink
# Compatible Windows Git Bash / Linux / Mac

echo "🚀 Lancement de VerseLink"
echo "========================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Fonction pour vérifier si un port est utilisé
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:$port >/dev/null 2>&1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -an | grep ":$port " >/dev/null 2>&1
    else
        return 1
    fi
}

# Fonction pour tuer un processus sur un port
kill_port() {
    local port=$1
    echo -e "${YELLOW}Arrêt du processus sur le port $port...${NC}"
    
    if command -v lsof >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            kill -9 $pid 2>/dev/null
            echo -e "${GREEN}Processus $pid arrêté.${NC}"
        fi
    elif command -v taskkill >/dev/null 2>&1; then
        # Windows
        for /f "tokens=5" %a in ('netstat -aon ^| findstr :$port') do taskkill /f /pid %a 2>nul
    fi
}

# Vérifications préliminaires
echo -e "${BLUE}1. Vérifications préliminaires...${NC}"

# Vérifier Python
if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ Python n'est pas installé!${NC}"
    exit 1
fi

PYTHON_CMD="python"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}✅ Python trouvé: $($PYTHON_CMD --version)${NC}"

# Vérifier Node.js
if ! command -v node >/dev/null 2>&1; then
    echo -e "${RED}❌ Node.js n'est pas installé!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js trouvé: $(node --version)${NC}"

# Vérifier MongoDB
if ! command -v mongod >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ MongoDB non trouvé dans PATH. Assurez-vous qu'il est installé et démarré.${NC}"
fi

# Créer les fichiers .env si ils n'existent pas
echo -e "${BLUE}2. Configuration des variables d'environnement...${NC}"

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}Création du fichier backend/.env...${NC}"
    cat > "$BACKEND_DIR/.env" << 'EOF'
MONGO_URL=mongodb://localhost:27017/verselink
JWT_SECRET_KEY=UnTresLongSecretAleatoire123
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DISCORD_CLIENT_ID=1413780341084131338
DISCORD_CLIENT_SECRET=VOTRE_DISCORD_CLIENT_SECRET
DISCORD_REDIRECT_URI=http://89.88.206.99:3000/auth/discord/callback
DISCORD_BOT_WEBHOOK_SECRET=your-discord-webhook-secret

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

APP_NAME=VerseLink
APP_VERSION=1.0.0
DEBUG=True
EOF
    echo -e "${GREEN}✅ Fichier backend/.env créé${NC}"
else
    echo -e "${GREEN}✅ Fichier backend/.env existe${NC}"
fi

if [ ! -f "$FRONTEND_DIR/.env" ]; then
    echo -e "${YELLOW}Création du fichier frontend/.env...${NC}"
    cat > "$FRONTEND_DIR/.env" << 'EOF'
REACT_APP_BACKEND_URL=http://89.88.206.99:8001
REACT_APP_NAME=VerseLink
REACT_APP_VERSION=1.0.0
EOF
    echo -e "${GREEN}✅ Fichier frontend/.env créé${NC}"
else
    echo -e "${GREEN}✅ Fichier frontend/.env existe${NC}"
fi

# Installation des dépendances
echo -e "${BLUE}3. Installation des dépendances...${NC}"

echo -e "${YELLOW}Installation des dépendances Python...${NC}"
cd "$BACKEND_DIR"
if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements.txt
else
    echo -e "${RED}❌ Fichier requirements.txt non trouvé!${NC}"
    exit 1
fi

echo -e "${YELLOW}Installation des dépendances Node.js...${NC}"
cd "$FRONTEND_DIR"
if [ -f "package.json" ]; then
    if command -v yarn >/dev/null 2>&1; then
        yarn install
    else
        npm install
    fi
else
    echo -e "${RED}❌ Fichier package.json non trouvé!${NC}"
    exit 1
fi

# Vérifier et arrêter les processus existants
echo -e "${BLUE}4. Vérification des ports...${NC}"

if check_port 8001; then
    echo -e "${YELLOW}Port 8001 (Backend) occupé${NC}"
    kill_port 8001
fi

if check_port 3000; then
    echo -e "${YELLOW}Port 3000 (Frontend) occupé${NC}"
    kill_port 3000
fi

# Lancement des services
echo -e "${BLUE}5. Lancement des services...${NC}"

# Créer un dossier pour les logs
mkdir -p "$PROJECT_DIR/logs"

# Lancer MongoDB si pas déjà lancé
if ! check_port 27017; then
    echo -e "${YELLOW}Tentative de lancement de MongoDB...${NC}"
    if command -v mongod >/dev/null 2>&1; then
        mongod --dbpath "$PROJECT_DIR/data/db" --logpath "$PROJECT_DIR/logs/mongodb.log" --fork 2>/dev/null || true
    fi
fi

# Lancer le backend
echo -e "${YELLOW}Lancement du backend (port 8001)...${NC}"
cd "$BACKEND_DIR"
$PYTHON_CMD server.py > "$PROJECT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend lancé (PID: $BACKEND_PID)${NC}"

# Attendre que le backend soit prêt
echo -e "${YELLOW}Attente du démarrage du backend...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8001/api/v1/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend prêt!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done
echo

# Lancer le frontend
echo -e "${YELLOW}Lancement du frontend (port 3000)...${NC}"
cd "$FRONTEND_DIR"
if command -v yarn >/dev/null 2>&1; then
    yarn start > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
else
    npm start > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
fi
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend lancé (PID: $FRONTEND_PID)${NC}"

# Attendre que le frontend soit prêt
echo -e "${YELLOW}Attente du démarrage du frontend...${NC}"
for i in {1..60}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend prêt!${NC}"
        break
    fi
    sleep 2
    echo -n "."
done
echo

# Résumé
echo
echo -e "${GREEN}🎉 VerseLink est maintenant lancé!${NC}"
echo "=================================="
echo -e "${BLUE}Frontend:${NC} http://89.88.206.99:3000"
echo -e "${BLUE}Backend:${NC}  http://89.88.206.99:8001"
echo -e "${BLUE}API Docs:${NC} http://89.88.206.99:8001/docs"
echo
echo -e "${YELLOW}Logs disponibles dans:${NC}"
echo "- Backend: $PROJECT_DIR/logs/backend.log"
echo "- Frontend: $PROJECT_DIR/logs/frontend.log"
echo
echo -e "${YELLOW}Pour arrêter les services:${NC}"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo
echo -e "${YELLOW}PIDs sauvegardés dans:${NC}"
echo "$BACKEND_PID" > "$PROJECT_DIR/.backend_pid"
echo "$FRONTEND_PID" > "$PROJECT_DIR/.frontend_pid"

# Ouvrir le navigateur (optionnel)
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://89.88.206.99:3000" 2>/dev/null &
elif command -v open >/dev/null 2>&1; then
    open "http://89.88.206.99:3000" 2>/dev/null &
elif command -v start >/dev/null 2>&1; then
    start "http://89.88.206.99:3000" 2>/dev/null &
fi

echo -e "${GREEN}✅ Script terminé. VerseLink fonctionne!${NC}"