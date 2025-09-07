import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ChatBubbleLeftRightIcon,
  ServerIcon,
  BellIcon,
  Cog6ToothIcon,
  PlusIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { discordService } from '../services/discordService';
import { useAuth } from '../App';

const DiscordIntegrationPage = () => {
  const [guilds, setGuilds] = useState([]);
  const [stats, setStats] = useState({});
  const [health, setHealth] = useState({});
  const [loading, setLoading] = useState(true);
  const [showAddGuild, setShowAddGuild] = useState(false);
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load guilds
      const guildsData = await discordService.getGuilds();
      setGuilds(guildsData);
      
      // Load health
      const healthData = await discordService.getHealth();
      setHealth(healthData);
      
      // Load stats if admin
      if (user && user.is_site_admin) {
        try {
          const statsData = await discordService.getStats();
          setStats(statsData);
        } catch (error) {
          // Ignore if not admin
        }
      }
      
    } catch (error) {
      console.error('Failed to load Discord data:', error);
      toast.error('Erreur lors du chargement des données Discord');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'text-green-400 bg-green-900/20 border-green-500/30';
      case 'inactive':
        return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
      case 'suspended':
        return 'text-red-400 bg-red-900/20 border-red-500/30';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'inactive':
        return <ClockIcon className="w-5 h-5" />;
      case 'suspended':
        return <XCircleIcon className="w-5 h-5" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5" />;
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <ChatBubbleLeftRightIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Connexion requise</h2>
          <p className="text-gray-400 mb-6">
            Connectez-vous pour accéder aux intégrations Discord.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
          >
            Se connecter
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Intégrations Discord</h1>
              <p className="text-gray-400 mt-2">
                Gérez vos serveurs Discord et configurez les intégrations VerseLink
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowAddGuild(true)}
                className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Ajouter un serveur
              </button>
              
              {user && user.is_site_admin && (
                <Link
                  to="/admin/discord/jobs"
                  className="inline-flex items-center px-4 py-2 border border-primary-600 rounded-lg text-primary-400 hover:bg-primary-600 hover:text-white transition-colors duration-200"
                >
                  <Cog6ToothIcon className="w-5 h-5 mr-2" />
                  Gestion des tâches
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Health Status */}
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${health.status === 'healthy' ? 'bg-green-900/20' : 'bg-red-900/20'}`}>
                {health.status === 'healthy' ? (
                  <CheckCircleIcon className="w-6 h-6 text-green-400" />
                ) : (
                  <ExclamationTriangleIcon className="w-6 h-6 text-red-400" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  État du système Discord
                </h3>
                <p className={`text-sm ${health.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                  {health.status === 'healthy' ? 'Opérationnel' : 'Problème détecté'}
                </p>
              </div>
            </div>
            
            <div className="text-right text-sm text-gray-400">
              <div>Configuration webhook: {health.webhook_secret_configured ? '✅' : '❌'}</div>
              <div>API bot configurée: {health.bot_api_configured ? '✅' : '❌'}</div>
              <div>Serveurs actifs: {health.active_guilds || 0}/{health.guilds_registered || 0}</div>
              {health.pending_jobs > 0 && (
                <div className="text-yellow-400">
                  {health.pending_jobs} tâche(s) en attente
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Statistics (Admin only) */}
        {user && user.is_site_admin && Object.keys(stats).length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <div className="flex items-center">
                <ServerIcon className="w-8 h-8 text-blue-400" />
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-white">{stats.total_guilds}</p>
                  <p className="text-gray-400">Serveurs totaux</p>
                </div>
              </div>
            </div>
            
            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <div className="flex items-center">
                <ClockIcon className="w-8 h-8 text-yellow-400" />
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-white">{stats.pending_jobs}</p>
                  <p className="text-gray-400">Tâches en attente</p>
                </div>
              </div>
            </div>
            
            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <div className="flex items-center">
                <ChatBubbleLeftRightIcon className="w-8 h-8 text-green-400" />
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-white">{stats.total_webhooks_sent}</p>
                  <p className="text-gray-400">Webhooks envoyés</p>
                </div>
              </div>
            </div>
            
            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <div className="flex items-center">
                <ChartBarIcon className="w-8 h-8 text-purple-400" />
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-white">{stats.recent_jobs}</p>
                  <p className="text-gray-400">Activité 24h</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Guilds List */}
        <div className="bg-dark-800 rounded-lg border border-dark-700">
          <div className="px-6 py-4 border-b border-dark-700">
            <h3 className="text-lg font-semibold text-white">Serveurs Discord intégrés</h3>
          </div>
          
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="loading-spinner w-8 h-8"></div>
            </div>
          ) : guilds.length > 0 ? (
            <div className="divide-y divide-dark-700">
              {guilds.map((guild) => (
                <div key={guild.id} className="p-6 hover:bg-dark-750 transition-colors duration-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-primary-900/20 rounded-lg">
                        <ServerIcon className="w-6 h-6 text-primary-400" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h4 className="text-white font-semibold text-lg">
                            {guild.guild_name}
                          </h4>
                          
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(guild.status)}`}>
                            {getStatusIcon(guild.status)}
                            <span className="ml-1">
                              {guild.status === 'active' ? 'Actif' : 
                               guild.status === 'inactive' ? 'Inactif' : 
                               guild.status === 'suspended' ? 'Suspendu' : guild.status}
                            </span>
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-400">
                          <span>ID: {guild.guild_id}</span>
                          {guild.org_name && (
                            <span className="text-primary-400">
                              🏢 {guild.org_name}
                            </span>
                          )}
                          <span>
                            Webhook: {guild.webhook_verified ? '✅ Vérifié' : '❌ Non vérifié'}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                          <span>
                            Sync: {guild.sync_enabled ? '✅' : '❌'}
                          </span>
                          <span>
                            Rappels: {guild.reminder_enabled ? '✅' : '❌'}
                          </span>
                          {guild.last_sync_at && (
                            <span>
                              Dernière sync: {new Date(guild.last_sync_at).toLocaleDateString('fr-FR')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toast('Configuration du serveur (bientôt disponible)', {
                          icon: 'ℹ️',
                          duration: 3000
                        })}
                        className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-dark-700 transition-colors duration-200"
                        title="Configurer le serveur"
                      >
                        <Cog6ToothIcon className="w-5 h-5" />
                      </button>
                      
                      <button
                        onClick={() => toast.info('Test de connexion (bientôt disponible)')}
                        className="px-3 py-2 text-sm border border-primary-600 text-primary-400 rounded-lg hover:bg-primary-600 hover:text-white transition-colors duration-200"
                      >
                        Tester
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <ServerIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-400 mb-2">
                Aucun serveur Discord intégré
              </h3>
              <p className="text-gray-500 mb-6">
                Ajoutez votre premier serveur Discord pour commencer à utiliser les intégrations VerseLink.
              </p>
              <button
                onClick={() => setShowAddGuild(true)}
                className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Ajouter un serveur Discord
              </button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            to="/discord/announcements"
            className="bg-dark-800 rounded-lg p-6 border border-dark-700 hover:border-primary-500 transition-colors duration-200 group"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-900/20 rounded-lg group-hover:bg-blue-600/20 transition-colors duration-200">
                <BellIcon className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h4 className="text-white font-semibold">Annonces</h4>
                <p className="text-gray-400 text-sm">
                  Gérer les annonces d'événements et tournois
                </p>
              </div>
            </div>
          </Link>
          
          <Link
            to="/discord/sync"
            className="bg-dark-800 rounded-lg p-6 border border-dark-700 hover:border-primary-500 transition-colors duration-200 group"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-green-900/20 rounded-lg group-hover:bg-green-600/20 transition-colors duration-200">
                <ChatBubbleLeftRightIcon className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <h4 className="text-white font-semibold">Synchronisation</h4>
                <p className="text-gray-400 text-sm">
                  Synchroniser les messages entre serveurs
                </p>
              </div>
            </div>
          </Link>
          
          <Link
            to="/discord/reminders"
            className="bg-dark-800 rounded-lg p-6 border border-dark-700 hover:border-primary-500 transition-colors duration-200 group"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-purple-900/20 rounded-lg group-hover:bg-purple-600/20 transition-colors duration-200">
                <ClockIcon className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <h4 className="text-white font-semibold">Rappels</h4>
                <p className="text-gray-400 text-sm">
                  Configurer les rappels automatiques
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* Add Guild Modal Placeholder */}
        {showAddGuild && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-dark-800 rounded-lg max-w-md w-full p-6 border border-dark-600">
              <h3 className="text-lg font-semibold text-white mb-4">
                Ajouter un serveur Discord
              </h3>
              <p className="text-gray-300 mb-6">
                Cette fonctionnalité sera bientôt disponible. Pour l'instant, utilisez l'API backend directement pour enregistrer vos serveurs Discord.
              </p>
              
              <div className="text-right">
                <button
                  onClick={() => setShowAddGuild(false)}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiscordIntegrationPage;