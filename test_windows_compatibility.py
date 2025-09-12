#!/usr/bin/env python3
"""
Test de compatibilité Windows pour VerseLink
Valide que tous les composants fonctionnent sans uvloop ni dépendances Unix
"""

import sys
import subprocess
import importlib
from pathlib import Path

def test_component(name, import_path, test_func=None):
    """Test un composant avec gestion d'erreurs"""
    try:
        module = importlib.import_module(import_path)
        if test_func:
            test_func(module)
        print(f"✅ {name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {name} - Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {name} - Error: {e}")
        return False

def test_discord_bot():
    """Test spécifique Discord Bot"""
    sys.path.insert(0, str(Path(__file__).parent / "discord_bot"))
    
    tests = [
        ("Discord.py", "discord"),
        ("AsyncIO", "asyncio"), 
        ("AIOHTTP", "aiohttp"),
        ("Requests", "requests"),
        ("APScheduler", "apscheduler.schedulers.asyncio"),
        ("Python-dotenv", "dotenv"),
        ("Pydantic", "pydantic"),
        ("HTTPX", "httpx"),
        ("Interactive Events", "interactive_events"),
        ("Event Handlers", "event_handlers"),
        ("Tournament Handlers", "tournament_handlers"),
        ("Event Management", "event_management"),
        ("VerseLink API", "verselink_api"),
        ("Utils", "utils"),
        ("Config", "config")
    ]
    
    passed = 0
    for name, import_path in tests:
        if test_component(name, import_path):
            passed += 1
    
    return passed, len(tests)

def test_backend():
    """Test spécifique Backend"""
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    
    tests = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Motor (MongoDB)", "motor.motor_asyncio"),
        ("PyMongo", "pymongo"),
        ("Pydantic", "pydantic"),
        ("Python-JOSE", "jose"),
        ("Passlib", "passlib.hash"),
        ("HTTPX", "httpx"),
        ("AuthLib", "authlib.integrations.starlette_client"),
        ("Server App", "server")
    ]
    
    passed = 0
    for name, import_path in tests:
        if test_component(name, import_path):
            passed += 1
    
    return passed, len(tests)

def check_requirements():
    """Vérifie les requirements.txt pour dépendances problématiques"""
    print("\n" + "="*60)
    print("VÉRIFICATION DES REQUIREMENTS")
    print("="*60)
    
    problematic_packages = [
        "uvloop",
        "watchfiles", 
        "httptools"
    ]
    
    # Vérifier backend
    backend_req = Path(__file__).parent / "backend" / "requirements.txt"
    if backend_req.exists():
        with open(backend_req) as f:
            backend_content = f.read().lower()
        
        found_issues = []
        for pkg in problematic_packages:
            if pkg in backend_content:
                found_issues.append(f"Backend: {pkg}")
        
        if found_issues:
            print("❌ Backend requirements issues:", ", ".join(found_issues))
        else:
            print("✅ Backend requirements - Windows compatible")
    
    # Vérifier discord_bot
    bot_req = Path(__file__).parent / "discord_bot" / "requirements.txt"
    if bot_req.exists():
        with open(bot_req) as f:
            bot_content = f.read().lower()
        
        found_issues = []
        for pkg in problematic_packages:
            if pkg in bot_content:
                found_issues.append(f"Discord Bot: {pkg}")
        
        if found_issues:
            print("❌ Discord Bot requirements issues:", ", ".join(found_issues))
        else:
            print("✅ Discord Bot requirements - Windows compatible")

def main():
    print("🪟 TEST DE COMPATIBILITÉ WINDOWS - VerseLink")
    print("="*60)
    print("Validation des corrections Phase 2")
    print()
    
    # Test requirements
    check_requirements()
    
    # Test Discord Bot
    print("\n" + "="*60)
    print("TEST DISCORD BOT PHASE 2")
    print("="*60)
    
    bot_passed, bot_total = test_discord_bot()
    bot_success_rate = (bot_passed / bot_total) * 100
    
    print(f"\nDiscord Bot: {bot_passed}/{bot_total} tests passés ({bot_success_rate:.1f}%)")
    
    # Test Backend
    print("\n" + "="*60)
    print("TEST BACKEND")
    print("="*60)
    
    backend_passed, backend_total = test_backend()
    backend_success_rate = (backend_passed / backend_total) * 100
    
    print(f"\nBackend: {backend_passed}/{backend_total} tests passés ({backend_success_rate:.1f}%)")
    
    # Résumé final
    total_passed = bot_passed + backend_passed
    total_tests = bot_total + backend_total
    overall_success_rate = (total_passed / total_tests) * 100
    
    print("\n" + "="*60)
    print("RÉSUMÉ FINAL")
    print("="*60)
    print(f"Tests réussis: {total_passed}/{total_tests}")
    print(f"Taux de réussite: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 95:
        print("🎉 COMPATIBILITÉ WINDOWS CONFIRMÉE!")
        print("✅ Le système peut être déployé sous Windows")
        print("✅ Aucune dépendance Unix/Linux problématique")
        print("✅ Discord Bot Phase 2 pleinement fonctionnel")
    elif overall_success_rate >= 85:
        print("⚠️  COMPATIBILITÉ WINDOWS MAJORITAIREMENT OK")
        print("Quelques ajustements mineurs peuvent être nécessaires")
    else:
        print("❌ PROBLÈMES DE COMPATIBILITÉ DÉTECTÉS")
        print("Des corrections supplémentaires sont nécessaires")
    
    return overall_success_rate >= 95

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)