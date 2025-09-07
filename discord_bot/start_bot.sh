#!/bin/bash
# Script de lancement du bot Discord VerseLink

echo "🤖 Lancement du Bot Discord VerseLink"
echo "====================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BOT_DIR"

# Vérifications préliminaires
echo -e "${BLUE}1. Vérifications...${NC}"

# Vérifier Python
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ Python 3 n'est pas installé!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"

# Vérifier le fichier .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ Fichier .env manquant, copie depuis .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 Veuillez éditer le fichier .env avec vos tokens avant de relancer.${NC}"
        exit 1
    else
        echo -e "${RED}❌ Fichier .env.example manquant!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Fichier .env trouvé${NC}"

# Vérifier les variables d'environnement
source .env
if [ -z "$DISCORD_BOT_TOKEN" ] || [ "$DISCORD_BOT_TOKEN" = "your_discord_bot_token_here" ]; then
    echo -e "${RED}❌ DISCORD_BOT_TOKEN non configuré dans .env${NC}"
    exit 1
fi

if [ -z "$VERSELINK_API_TOKEN" ] || [ "$VERSELINK_API_TOKEN" = "your_verselink_api_token_here" ]; then
    echo -e "${RED}❌ VERSELINK_API_TOKEN non configuré dans .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Variables d'environnement configurées${NC}"

# Installation des dépendances
echo -e "${BLUE}2. Installation des dépendances...${NC}"
pip3 install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✅ Dépendances installées${NC}"

# Test de connexion API
echo -e "${BLUE}3. Test de connexion API...${NC}"
python3 -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_base = os.getenv('VERSELINK_API_BASE')
api_token = os.getenv('VERSELINK_API_TOKEN')

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

try:
    response = requests.get(f'{api_base}/discord/health', headers=headers, timeout=10)
    if response.status_code == 200:
        print('✅ API VerseLink accessible')
    else:
        print(f'❌ API Error: {response.status_code}')
        exit(1)
except Exception as e:
    print(f'❌ Connection Error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Impossible de se connecter à l'API VerseLink${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API VerseLink accessible${NC}"

# Lancement du bot
echo -e "${BLUE}4. Lancement du bot...${NC}"
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter le bot${NC}"
echo ""

# Lancer le bot avec redirection des logs
python3 bot.py 2>&1 | tee bot.log

echo -e "${YELLOW}👋 Bot arrêté${NC}"