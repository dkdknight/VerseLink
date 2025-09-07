#!/bin/bash
# Script de vérification d'état VerseLink

echo "📊 État de VerseLink"
echo "==================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour vérifier si un port est utilisé
check_port() {
    local port=$1
    local service=$2
    
    if command -v lsof >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            echo -e "${GREEN}✅ $service (Port $port) - Actif (PID: $pid)${NC}"
            return 0
        else
            echo -e "${RED}❌ $service (Port $port) - Inactif${NC}"
            return 1
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an | grep ":$port " >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service (Port $port) - Actif${NC}"
            return 0
        else
            echo -e "${RED}❌ $service (Port $port) - Inactif${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️ $service (Port $port) - Impossible de vérifier${NC}"
        return 1
    fi
}

# Fonction pour tester la connectivité HTTP
test_http() {
    local url=$1
    local service=$2
    
    if command -v curl >/dev/null 2>&1; then
        if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service HTTP - Répond${NC}"
            return 0
        else
            echo -e "${RED}❌ $service HTTP - Ne répond pas${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️ $service HTTP - curl non disponible${NC}"
        return 1
    fi
}

echo -e "${BLUE}Services réseau:${NC}"
check_port 27017 "MongoDB"
check_port 8001 "Backend (FastAPI)"
check_port 3000 "Frontend (React)"

echo
echo -e "${BLUE}Tests de connectivité:${NC}"
test_http "http://localhost:8001/api/v1/health" "Backend API"
test_http "http://localhost:3000" "Frontend"

echo
echo -e "${BLUE}URLs d'accès:${NC}"
echo -e "${YELLOW}Frontend local:${NC}   http://localhost:3000"
echo -e "${YELLOW}Frontend externe:${NC} http://89.88.206.99:3000"
echo -e "${YELLOW}Backend local:${NC}    http://localhost:8001"
echo -e "${YELLOW}Backend externe:${NC}  http://89.88.206.99:8001"
echo -e "${YELLOW}API Documentation:${NC} http://89.88.206.99:8001/docs"

echo
echo -e "${BLUE}Processus actifs:${NC}"
if command -v ps >/dev/null 2>&1; then
    echo -e "${YELLOW}Python/Backend:${NC}"
    ps aux | grep -E "(server\.py|uvicorn)" | grep -v grep || echo "Aucun processus Python backend trouvé"
    
    echo -e "${YELLOW}Node.js/Frontend:${NC}"
    ps aux | grep -E "(react-scripts|webpack|node.*start)" | grep -v grep || echo "Aucun processus Node.js frontend trouvé"
    
    echo -e "${YELLOW}MongoDB:${NC}"
    ps aux | grep mongod | grep -v grep || echo "MongoDB non trouvé dans les processus"
fi

echo
echo -e "${BLUE}Logs récents:${NC}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$PROJECT_DIR/logs/backend.log" ]; then
    echo -e "${YELLOW}Backend (dernières 3 lignes):${NC}"
    tail -3 "$PROJECT_DIR/logs/backend.log" 2>/dev/null || echo "Impossible de lire le log backend"
fi

if [ -f "$PROJECT_DIR/logs/frontend.log" ]; then
    echo -e "${YELLOW}Frontend (dernières 3 lignes):${NC}"
    tail -3 "$PROJECT_DIR/logs/frontend.log" 2>/dev/null || echo "Impossible de lire le log frontend"
fi

echo
echo -e "${GREEN}Vérification terminée!${NC}"