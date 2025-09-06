#!/bin/bash
# Script d'arrêt VerseLink

echo "🛑 Arrêt de VerseLink"
echo "===================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fonction pour tuer un processus sur un port
kill_port() {
    local port=$1
    echo -e "${YELLOW}Arrêt du processus sur le port $port...${NC}"
    
    if command -v lsof >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            kill -15 $pid 2>/dev/null
            sleep 2
            kill -9 $pid 2>/dev/null
            echo -e "${GREEN}✅ Processus sur port $port arrêté.${NC}"
        else
            echo -e "${YELLOW}Aucun processus sur le port $port${NC}"
        fi
    elif command -v netstat >/dev/null 2>&1; then
        # Windows/Linux fallback
        local pid=$(netstat -ano | grep ":$port " | awk '{print $5}' | head -1)
        if [ ! -z "$pid" ] && [ "$pid" != "0" ]; then
            if command -v taskkill >/dev/null 2>&1; then
                taskkill /f /pid $pid 2>/dev/null
            else
                kill -9 $pid 2>/dev/null
            fi
            echo -e "${GREEN}✅ Processus $pid arrêté.${NC}"
        fi
    fi
}

# Lire les PIDs sauvegardés
if [ -f "$PROJECT_DIR/.backend_pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_DIR/.backend_pid")
    echo -e "${YELLOW}Arrêt du backend (PID: $BACKEND_PID)...${NC}"
    kill -15 $BACKEND_PID 2>/dev/null
    sleep 2
    kill -9 $BACKEND_PID 2>/dev/null
    rm -f "$PROJECT_DIR/.backend_pid"
    echo -e "${GREEN}✅ Backend arrêté${NC}"
fi

if [ -f "$PROJECT_DIR/.frontend_pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_DIR/.frontend_pid")
    echo -e "${YELLOW}Arrêt du frontend (PID: $FRONTEND_PID)...${NC}"
    kill -15 $FRONTEND_PID 2>/dev/null
    sleep 2
    kill -9 $FRONTEND_PID 2>/dev/null
    rm -f "$PROJECT_DIR/.frontend_pid"
    echo -e "${GREEN}✅ Frontend arrêté${NC}"
fi

# Arrêter les processus sur les ports standard
kill_port 8001  # Backend
kill_port 3000  # Frontend

# Nettoyer les processus Node.js et Python restants
echo -e "${YELLOW}Nettoyage des processus restants...${NC}"
pkill -f "server.py" 2>/dev/null
pkill -f "react-scripts" 2>/dev/null
pkill -f "webpack" 2>/dev/null

echo -e "${GREEN}🎉 VerseLink arrêté complètement!${NC}"