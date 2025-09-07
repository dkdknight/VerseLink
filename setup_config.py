#!/usr/bin/env python3
"""
Script de configuration automatique pour VerseLink
Configure les fichiers .env selon config.json
"""

import json
import os
from pathlib import Path

def load_config():
    """Charger la configuration depuis config.json"""
    config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        print("❌ Fichier config.json introuvable !")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_backend_env(config):
    """Mettre à jour le fichier .env du backend"""
    backend_env_path = Path(__file__).parent / "backend" / ".env"
    
    # Demander le Discord Client Secret si pas défini
    discord_secret = input("Entrez votre DISCORD_CLIENT_SECRET (ou laissez vide pour garder actuel): ").strip()
    if not discord_secret:
        discord_secret = "VOTRE_DISCORD_CLIENT_SECRET_ICI"
    
    env_content = f"""MONGO_URL={config['database']['mongo_url']}
JWT_SECRET_KEY={config['jwt']['secret_key']}
JWT_ALGORITHM={config['jwt']['algorithm']}
ACCESS_TOKEN_EXPIRE_MINUTES={config['jwt']['expire_minutes']}

DISCORD_CLIENT_ID={config['discord']['client_id']}
DISCORD_CLIENT_SECRET={discord_secret}
DISCORD_REDIRECT_URI={config['discord']['redirect_uri']}
DISCORD_BOT_WEBHOOK_SECRET=your-discord-webhook-secret

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

APP_NAME=VerseLink
APP_VERSION=1.0.0
DEBUG=True

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
"""
    
    with open(backend_env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Backend .env mis à jour : {backend_env_path}")

def update_frontend_env(config):
    """Mettre à jour le fichier .env du frontend"""
    frontend_env_path = Path(__file__).parent / "frontend" / ".env"
    
    env_content = f"""REACT_APP_BACKEND_URL={config['urls']['backend_url']}
REACT_APP_NAME=VerseLink
REACT_APP_VERSION=1.0.0
"""
    
    with open(frontend_env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Frontend .env mis à jour : {frontend_env_path}")

def update_cors_config(config):
    """Mettre à jour la configuration CORS dans server.py"""
    server_py_path = Path(__file__).parent / "backend" / "server.py"
    
    if not server_py_path.exists():
        print("❌ Fichier server.py introuvable !")
        return
    
    # Lire le contenu actuel
    with open(server_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver et remplacer la configuration CORS
    old_cors = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
    
    new_cors = f"""app.add_middleware(
    CORSMiddleware,
    allow_origins=["{config['urls']['frontend_url']}", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
    
    if old_cors in content:
        content = content.replace(old_cors, new_cors)
        
        with open(server_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Configuration CORS mise à jour dans server.py")
    else:
        print("⚠️ Configuration CORS non trouvée dans server.py")

def display_config_summary(config):
    """Afficher un résumé de la configuration"""
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DE LA CONFIGURATION")
    print("="*60)
    print(f"🌐 Frontend URL    : {config['urls']['frontend_url']}")
    print(f"🔧 Backend URL     : {config['urls']['backend_url']}")
    print(f"🔗 Discord Redirect: {config['discord']['redirect_uri']}")
    print(f"💾 Database        : {config['database']['mongo_url']}")
    print(f"🎯 Environment     : {config['environment']}")
    print("="*60)

def main():
    print("🚀 Configuration automatique VerseLink")
    print("="*50)
    
    # Charger la configuration
    config = load_config()
    if not config:
        return
    
    # Afficher la configuration
    display_config_summary(config)
    
    # Demander confirmation
    confirm = input("\\n🤔 Voulez-vous appliquer cette configuration ? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', 'o', 'oui']:
        print("❌ Configuration annulée.")
        return
    
    # Appliquer les configurations
    print("\\n🔧 Application de la configuration...")
    update_backend_env(config)
    update_frontend_env(config)
    update_cors_config(config)
    
    print("\\n✅ Configuration terminée !")
    print("\\n📋 PROCHAINES ÉTAPES :")
    print("1. Configurez votre DISCORD_CLIENT_SECRET dans Discord Developer Portal")
    print("2. Ajoutez cette URL de redirection Discord :")
    print(f"   {config['discord']['redirect_uri']}")
    print("3. Redémarrez les services :")
    print("   sudo supervisorctl restart all")

if __name__ == "__main__":
    main()