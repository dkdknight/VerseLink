import React, { useState, useEffect } from 'react';
import { discordService } from '../services/discordService';
import DiscordTestButton from './DiscordTestButton';
import { toast } from 'react-hot-toast';

const OrganizationDiscordConfig = ({ orgId, orgName, isAdmin = false }) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    discord_guild_id: '',
    discord_guild_name: '',
    events_channel_id: '',
    events_channel_name: '',
    tournaments_channel_id: '',
    tournaments_channel_name: '',
    auto_publish_events: true,
    auto_publish_tournaments: true
  });

  useEffect(() => {
    loadConfig();
  }, [orgId]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const configData = await discordService.getDiscordConfig(orgId);
      if (configData) {
        setConfig(configData);
        setFormData(configData);
      }
    } catch (error) {
      console.error('Failed to load Discord config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const updatedConfig = await discordService.updateDiscordConfig(orgId, formData);
      setConfig(updatedConfig.config);
      setEditing(false);
      toast.success('Configuration Discord mise à jour !');
    } catch (error) {
      console.error('Failed to save Discord config:', error);
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-full"></div>
            <div className="h-4 bg-gray-700 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!config && !isAdmin) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-center">
          <div className="text-gray-400 mb-2">🔧</div>
          <h3 className="text-lg font-semibold text-white mb-2">Discord non configuré</h3>
          <p className="text-gray-400">
            Cette organisation n'a pas encore configuré l'intégration Discord.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white flex items-center">
          <span className="text-discord mr-2">💬</span>
          Configuration Discord
        </h3>
        {isAdmin && config && !editing && (
          <button
            onClick={() => setEditing(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            ✏️ Modifier
          </button>
        )}
      </div>

      {!config ? (
        // Première configuration
        <div className="space-y-6">
          <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-4">
            <h4 className="text-blue-400 font-semibold mb-2">🚀 Première configuration</h4>
            <p className="text-blue-300 text-sm mb-3">
              Pour activer la publication automatique d'événements sur Discord, configurez les informations suivantes :
            </p>
            <ol className="text-blue-300 text-sm space-y-1 list-decimal list-inside">
              <li>ID du serveur Discord de votre organisation</li>
              <li>ID du canal pour les événements</li>
              <li>ID du canal pour les tournois (optionnel)</li>
            </ol>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ID du serveur Discord *
              </label>
              <input
                type="text"
                value={formData.discord_guild_id}
                onChange={(e) => handleInputChange('discord_guild_id', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="123456789012345678"
              />
              <p className="text-gray-400 text-xs mt-1">
                Clic droit sur votre serveur Discord → Copier l'ID
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Nom du serveur Discord *
              </label>
              <input
                type="text"
                value={formData.discord_guild_name}
                onChange={(e) => handleInputChange('discord_guild_name', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Mon Organisation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ID canal événements *
              </label>
              <input
                type="text"
                value={formData.events_channel_id}
                onChange={(e) => handleInputChange('events_channel_id', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="987654321098765432"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Nom canal événements *
              </label>
              <input
                type="text"
                value={formData.events_channel_name}
                onChange={(e) => handleInputChange('events_channel_name', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="événements"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ID canal tournois (optionnel)
              </label>
              <input
                type="text"
                value={formData.tournaments_channel_id}
                onChange={(e) => handleInputChange('tournaments_channel_id', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="111222333444555666"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Nom canal tournois (optionnel)
              </label>
              <input
                type="text"
                value={formData.tournaments_channel_name}
                onChange={(e) => handleInputChange('tournaments_channel_name', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="tournois"
              />
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleSave}
              disabled={saving || !formData.discord_guild_id || !formData.events_channel_id}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-all duration-200 flex items-center space-x-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Sauvegarde...</span>
                </>
              ) : (
                <>
                  <span>💾</span>
                  <span>Sauvegarder</span>
                </>
              )}
            </button>
          </div>
        </div>
      ) : editing ? (
        // Mode édition
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ID du serveur Discord
              </label>
              <input
                type="text"
                value={formData.discord_guild_id}
                onChange={(e) => handleInputChange('discord_guild_id', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Nom du serveur
              </label>
              <input
                type="text"
                value={formData.discord_guild_name}
                onChange={(e) => handleInputChange('discord_guild_name', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ID canal événements
              </label>
              <input
                type="text"
                value={formData.events_channel_id}
                onChange={(e) => handleInputChange('events_channel_id', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ID canal tournois
              </label>
              <input
                type="text"
                value={formData.tournaments_channel_id}
                onChange={(e) => handleInputChange('tournaments_channel_id', e.target.value)}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={formData.auto_publish_events}
                onChange={(e) => handleInputChange('auto_publish_events', e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
              />
              <span className="text-gray-300">Publication automatique des événements</span>
            </label>

            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={formData.auto_publish_tournaments}
                onChange={(e) => handleInputChange('auto_publish_tournaments', e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
              />
              <span className="text-gray-300">Publication automatique des tournois</span>
            </label>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              {saving ? 'Sauvegarde...' : '💾 Sauvegarder'}
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setFormData(config);
              }}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              Annuler
            </button>
          </div>
        </div>
      ) : (
        // Mode lecture avec configuration existante
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Serveur Discord</h4>
              <p className="text-white font-medium">{config.discord_guild_name}</p>
              <p className="text-gray-400 text-sm">ID: {config.discord_guild_id}</p>
            </div>

            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Canal événements</h4>
              <p className="text-white font-medium">#{config.events_channel_name}</p>
              <p className="text-gray-400 text-sm">ID: {config.events_channel_id}</p>
            </div>

            {config.tournaments_channel_id && (
              <div className="bg-gray-700 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Canal tournois</h4>
                <p className="text-white font-medium">#{config.tournaments_channel_name}</p>
                <p className="text-gray-400 text-sm">ID: {config.tournaments_channel_id}</p>
              </div>
            )}

            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Publications automatiques</h4>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className={config.auto_publish_events ? 'text-green-400' : 'text-red-400'}>
                    {config.auto_publish_events ? '✅' : '❌'}
                  </span>
                  <span className="text-white text-sm">Événements</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={config.auto_publish_tournaments ? 'text-green-400' : 'text-red-400'}>
                    {config.auto_publish_tournaments ? '✅' : '❌'}
                  </span>
                  <span className="text-white text-sm">Tournois</span>
                </div>
              </div>
            </div>
          </div>

          {/* Tests de connexion */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-white">Tests de Connexion</h4>
            
            <div className="space-y-3">
              <DiscordTestButton 
                orgId={orgId} 
                orgName={orgName} 
                testType="connection"
              />
              
              <DiscordTestButton 
                orgId={orgId} 
                orgName={orgName} 
                testType="events_channel"
              />
              
              {config.tournaments_channel_id && config.tournaments_channel_id !== config.events_channel_id && (
                <DiscordTestButton 
                  orgId={orgId} 
                  orgName={orgName} 
                  testType="tournaments_channel"
                />
              )}
            </div>
          </div>

          <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
            <h4 className="text-green-400 font-semibold mb-2">🎉 Configuration Active</h4>
            <p className="text-green-300 text-sm">
              Les événements et tournois créés depuis le site web seront automatiquement publiés sur Discord !
              Les membres pourront s'inscrire directement via les réactions Discord.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrganizationDiscordConfig;