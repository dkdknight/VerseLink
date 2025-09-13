import discord
from discord.ext import commands
import logging
from aiohttp import web
import json
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from auto_publisher import AutoPublisher
from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Gestionnaire des webhooks entre le site web et Discord"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = VerselinkAPI()
        self.auto_publisher = AutoPublisher(bot)
        
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Vérifie la signature du webhook pour la sécurité"""
        if not signature or not secret:
            return False
            
        try:
            # Discord utilise sha256
            expected = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Signature format: "sha256=hash"
            if signature.startswith('sha256='):
                signature = signature[7:]
                
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def handle_event_created(self, request: web.Request) -> web.Response:
        """Gère la création d'événements depuis le site web"""
        try:
            # Lire le payload
            payload = await request.read()
            
            # Vérifier la signature si configurée
            signature = request.headers.get('X-Webhook-Signature')
            webhook_secret = Config.WEBHOOK_SECRET
            
            if webhook_secret and not self.verify_webhook_signature(payload, signature, webhook_secret):
                logger.warning("Invalid webhook signature for event creation")
                return web.json_response({'error': 'Invalid signature'}, status=401)
            
            # Parser les données
            data = json.loads(payload.decode('utf-8'))
            event_data = data.get('event')
            org_id = data.get('org_id')
            
            if not event_data or not org_id:
                return web.json_response({'error': 'Missing event data or org_id'}, status=400)
            
            logger.info(f"Received event creation webhook for event: {event_data.get('title')}")
            
            # Récupérer la configuration Discord de l'organisation
            async with self.api as api:
                org_config = await api.get_organization_discord_config(org_id)
                
                if not org_config:
                    logger.info(f"No Discord config for org {org_id}, skipping publication")
                    return web.json_response({'message': 'No Discord config found'}, status=200)
                
                if not org_config.get('auto_publish_events', True):
                    logger.info(f"Auto-publish disabled for org {org_id}")
                    return web.json_response({'message': 'Auto-publish disabled'}, status=200)
            
            # Publier l'événement sur Discord
            message = await self.auto_publisher.publish_event(event_data, org_config)
            
            if message:
                response_data = {
                    'success': True,
                    'message': 'Event published to Discord',
                    'discord_message_id': str(message.id),
                    'discord_channel_id': str(message.channel.id),
                    'discord_guild_id': str(message.guild.id)
                }
                logger.info(f"Event {event_data.get('title')} published to Discord successfully")
            else:
                response_data = {
                    'success': False,
                    'message': 'Failed to publish event to Discord'
                }
                logger.error(f"Failed to publish event {event_data.get('title')} to Discord")
            
            return web.json_response(response_data)
            
        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error handling event creation webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_tournament_created(self, request: web.Request) -> web.Response:
        """Gère la création de tournois depuis le site web"""
        try:
            payload = await request.read()
            
            # Vérifier la signature
            signature = request.headers.get('X-Webhook-Signature')
            webhook_secret = Config.WEBHOOK_SECRET
            
            if webhook_secret and not self.verify_webhook_signature(payload, signature, webhook_secret):
                logger.warning("Invalid webhook signature for tournament creation")
                return web.json_response({'error': 'Invalid signature'}, status=401)
            
            data = json.loads(payload.decode('utf-8'))
            tournament_data = data.get('tournament')
            org_id = data.get('org_id')
            
            if not tournament_data or not org_id:
                return web.json_response({'error': 'Missing tournament data or org_id'}, status=400)
            
            logger.info(f"Received tournament creation webhook for: {tournament_data.get('name')}")
            
            # Récupérer la configuration Discord
            async with self.api as api:
                org_config = await api.get_organization_discord_config(org_id)
                
                if not org_config or not org_config.get('auto_publish_tournaments', True):
                    return web.json_response({'message': 'Auto-publish disabled or no config'}, status=200)
            
            # Publier le tournoi
            message = await self.auto_publisher.publish_tournament(tournament_data, org_config)
            
            if message:
                response_data = {
                    'success': True,
                    'message': 'Tournament published to Discord',
                    'discord_message_id': str(message.id),
                    'discord_channel_id': str(message.channel.id),
                    'discord_guild_id': str(message.guild.id)
                }
            else:
                response_data = {
                    'success': False,
                    'message': 'Failed to publish tournament to Discord'
                }
            
            return web.json_response(response_data)
            
        except Exception as e:
            logger.error(f"Error handling tournament creation webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_test_connection(self, request: web.Request) -> web.Response:
        """Teste la connexion Discord pour une organisation"""
        try:
            payload = await request.read()
            
            # Vérification signature
            signature = request.headers.get('X-Webhook-Signature')
            webhook_secret = Config.WEBHOOK_SECRET
            
            if webhook_secret and not self.verify_webhook_signature(payload, signature, webhook_secret):
                return web.json_response({'error': 'Invalid signature'}, status=401)
            
            data = json.loads(payload.decode('utf-8'))
            org_id = data.get('org_id')
            test_type = data.get('test_type', 'connection')  # connection, events_channel, tournaments_channel
            
            if not org_id:
                return web.json_response({'error': 'Missing org_id'}, status=400)
            
            logger.info(f"Testing Discord connection for org {org_id}, test type: {test_type}")
            
            # Récupérer la configuration Discord
            async with self.api as api:
                org_config = await api.get_organization_discord_config(org_id)
                org_data = await api.get_organization(org_id)
                
                if not org_config:
                    return web.json_response({
                        'success': False,
                        'message': 'No Discord configuration found for this organization'
                    }, status=404)
            
            # Tests selon le type
            test_results = await self.run_discord_tests(org_config, org_data, test_type)
            
            return web.json_response(test_results)
            
        except Exception as e:
            logger.error(f"Error handling test connection webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def run_discord_tests(self, org_config: Dict[str, Any], org_data: Dict[str, Any], test_type: str) -> Dict[str, Any]:
        """Exécute les tests Discord selon le type"""
        results = {
            'success': True,
            'tests': [],
            'summary': ''
        }
        
        guild_id = org_config.get('discord_guild_id')
        guild = self.bot.get_guild(int(guild_id)) if guild_id else None
        
        # Test 1: Connexion au serveur
        if not guild:
            results['tests'].append({
                'name': 'Connexion serveur Discord',
                'success': False,
                'message': f'Impossible de se connecter au serveur Discord {guild_id}'
            })
            results['success'] = False
            return results
        
        results['tests'].append({
            'name': 'Connexion serveur Discord',
            'success': True,
            'message': f'Connecté à {guild.name} ({guild.member_count} membres)'
        })
        
        # Test 2: Canal événements
        events_channel_id = org_config.get('events_channel_id')
        if events_channel_id and (test_type in ['connection', 'events_channel']):
            events_channel = guild.get_channel(int(events_channel_id))
            
            if not events_channel:
                results['tests'].append({
                    'name': 'Canal événements',
                    'success': False,
                    'message': f'Canal événements #{events_channel_id} introuvable'
                })
                results['success'] = False
            else:
                # Vérifier les permissions
                perms = events_channel.permissions_for(guild.me)
                missing_perms = []
                
                if not perms.send_messages:
                    missing_perms.append('Envoyer des messages')
                if not perms.embed_links:
                    missing_perms.append('Intégrer des liens')
                if not perms.add_reactions:
                    missing_perms.append('Ajouter des réactions')
                if not perms.read_message_history:
                    missing_perms.append('Lire l\'historique')
                
                if missing_perms:
                    results['tests'].append({
                        'name': 'Permissions canal événements',
                        'success': False,
                        'message': f'Permissions manquantes: {", ".join(missing_perms)}'
                    })
                    results['success'] = False
                else:
                    results['tests'].append({
                        'name': 'Canal événements',
                        'success': True,
                        'message': f'Canal #{events_channel.name} accessible avec toutes les permissions'
                    })
                    
                    # Test d'envoi de message si demandé
                    if test_type == 'events_channel':
                        try:
                            test_embed = create_info_embed(
                                "🧪 Test de Connexion VerseLink",
                                f"Ce message confirme que VerseLink peut publier des événements dans ce canal.\n\n"
                                f"**Organisation :** {org_data.get('name', 'N/A')}\n"
                                f"**Serveur :** {guild.name}\n"
                                f"**Date du test :** <t:{int(datetime.now(timezone.utc).timestamp())}:F>\n\n"
                                f"✅ La publication automatique d'événements est opérationnelle !"
                            )
                            
                            message = await events_channel.send(embed=test_embed)
                            await message.add_reaction("✅")
                            
                            results['tests'].append({
                                'name': 'Test envoi message événements',
                                'success': True,
                                'message': f'Message de test envoyé avec succès',
                                'discord_message_link': f'https://discord.com/channels/{guild.id}/{events_channel.id}/{message.id}'
                            })
                            
                        except Exception as e:
                            results['tests'].append({
                                'name': 'Test envoi message événements',
                                'success': False,
                                'message': f'Erreur lors de l\'envoi: {str(e)}'
                            })
                            results['success'] = False
        
        # Test 3: Canal tournois (si différent)
        tournaments_channel_id = org_config.get('tournaments_channel_id')
        if (tournaments_channel_id and tournaments_channel_id != events_channel_id and 
            test_type in ['connection', 'tournaments_channel']):
            
            tournaments_channel = guild.get_channel(int(tournaments_channel_id))
            
            if not tournaments_channel:
                results['tests'].append({
                    'name': 'Canal tournois',
                    'success': False,
                    'message': f'Canal tournois #{tournaments_channel_id} introuvable'
                })
                results['success'] = False
            else:
                perms = tournaments_channel.permissions_for(guild.me)
                if not all([perms.send_messages, perms.embed_links, perms.add_reactions]):
                    results['tests'].append({
                        'name': 'Canal tournois',
                        'success': False,
                        'message': 'Permissions insuffisantes'
                    })
                    results['success'] = False
                else:
                    results['tests'].append({
                        'name': 'Canal tournois',
                        'success': True,
                        'message': f'Canal #{tournaments_channel.name} accessible'
                    })
                    
                    # Test d'envoi pour tournois
                    if test_type == 'tournaments_channel':
                        try:
                            test_embed = create_info_embed(
                                "🏆 Test Tournois VerseLink",
                                f"Test de publication de tournois réussi !\n\n"
                                f"**Organisation :** {org_data.get('name', 'N/A')}\n"
                                f"**Serveur :** {guild.name}\n\n"
                                f"✅ La publication automatique de tournois fonctionne parfaitement !"
                            )
                            
                            message = await tournaments_channel.send(embed=test_embed)
                            await message.add_reaction("🏆")
                            
                            results['tests'].append({
                                'name': 'Test envoi message tournois',
                                'success': True,
                                'message': 'Message de test tournoi envoyé',
                                'discord_message_link': f'https://discord.com/channels/{guild.id}/{tournaments_channel.id}/{message.id}'
                            })
                            
                        except Exception as e:
                            results['tests'].append({
                                'name': 'Test envoi message tournois',
                                'success': False,
                                'message': f'Erreur: {str(e)}'
                            })
                            results['success'] = False
        
        # Générer le résumé
        passed_tests = len([t for t in results['tests'] if t['success']])
        total_tests = len(results['tests'])
        
        if results['success']:
            results['summary'] = f'✅ Tous les tests réussis ({passed_tests}/{total_tests})'
        else:
            results['summary'] = f'⚠️ {passed_tests}/{total_tests} tests réussis - Vérifiez la configuration'
        
        return results
    
    async def notify_signup_to_backend(self, event_id: str, user_id: str, signup_data: Dict[str, Any]):
        """Notifie le backend d'une inscription via Discord"""
        try:
            async with self.api as api:
                # Envoyer la notification au backend
                notification_data = {
                    'event_id': event_id,
                    'user_id': user_id,
                    'signup_data': signup_data,
                    'source': 'discord',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                # Endpoint pour notifier les inscriptions Discord
                await api.notify_discord_signup(notification_data)
                logger.info(f"Notified backend of Discord signup for event {event_id}")
                
        except Exception as e:
            logger.error(f"Failed to notify backend of Discord signup: {e}")

def setup_webhook_routes(app: web.Application, webhook_handler: WebhookHandler):
    """Configure les routes webhook"""
    app.router.add_post('/webhook/event-created', webhook_handler.handle_event_created)
    app.router.add_post('/webhook/tournament-created', webhook_handler.handle_tournament_created)
    app.router.add_post('/webhook/test-connection', webhook_handler.handle_test_connection)
    
    # Route de santé
    async def health_check(request):
        return web.json_response({'status': 'ok', 'service': 'discord-webhook'})
    
    app.router.add_get('/webhook/health', health_check)