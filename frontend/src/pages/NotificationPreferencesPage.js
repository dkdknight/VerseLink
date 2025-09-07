import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon,
  BellIcon,
  EnvelopeIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { notificationService } from '../services/notificationService';
import { useAuth } from '../App';

const NotificationPreferencesPage = () => {
  const [preferences, setPreferences] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  const notificationTypes = [
    {
      category: 'Événements',
      types: [
        { key: 'event_created', label: 'Nouveaux événements', description: 'Quand un nouvel événement est créé dans vos organisations' },
        { key: 'event_updated', label: 'Événements mis à jour', description: 'Quand les détails d\'un événement changent' },
        { key: 'event_reminder', label: 'Rappels d\'événements', description: 'Rappels avant le début des événements inscrits' },
        { key: 'event_signup_confirmed', label: 'Inscriptions confirmées', description: 'Quand votre inscription à un événement est confirmée' },
        { key: 'event_checkin_available', label: 'Check-in disponible', description: 'Quand le check-in pour un événement s\'ouvre' }
      ]
    },
    {
      category: 'Tournois',
      types: [
        { key: 'tournament_created', label: 'Nouveaux tournois', description: 'Quand un nouveau tournoi est créé' },
        { key: 'tournament_started', label: 'Tournois commencés', description: 'Quand un tournoi auquel vous participez commence' },
        { key: 'team_invited', label: 'Invitations d\'équipe', description: 'Quand vous êtes invité à rejoindre une équipe' },
        { key: 'match_scheduled', label: 'Matchs programmés', description: 'Quand un de vos matchs est programmé' },
        { key: 'match_result', label: 'Résultats de matchs', description: 'Quand les résultats de vos matchs sont publiés' },
        { key: 'tournament_won', label: 'Victoires de tournoi', description: 'Quand vous remportez un tournoi' }
      ]
    },
    {
      category: 'Organisation',
      types: [
        { key: 'org_member_joined', label: 'Nouveaux membres', description: 'Quand quelqu\'un rejoint vos organisations (admins seulement)' },
        { key: 'org_role_changed', label: 'Changements de rôle', description: 'Quand votre rôle dans une organisation change' },
        { key: 'org_event_published', label: 'Événements publiés', description: 'Quand votre organisation publie un nouvel événement' }
      ]
    },
    {
      category: 'Modération',
      types: [
        { key: 'warning_received', label: 'Avertissements', description: 'Quand vous recevez un avertissement' },
        { key: 'strike_received', label: 'Strikes', description: 'Quand vous recevez un strike' },
        { key: 'reputation_changed', label: 'Changements de réputation', description: 'Quand votre réputation change' },
        { key: 'account_suspended', label: 'Suspension de compte', description: 'Quand votre compte est suspendu' }
      ]
    },
    {
      category: 'Système',
      types: [
        { key: 'welcome', label: 'Bienvenue', description: 'Messages de bienvenue pour les nouveaux utilisateurs' },
        { key: 'system_update', label: 'Mises à jour système', description: 'Informations sur les mises à jour de la plateforme' },
        { key: 'maintenance', label: 'Maintenance', description: 'Notifications de maintenance programmée' }
      ]
    }
  ];

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const data = await notificationService.getNotificationPreferences();
      setPreferences(data.preferences || {});
    } catch (error) {
      console.error('Failed to load preferences:', error);
      toast.error('Erreur lors du chargement des préférences');
    } finally {
      setLoading(false);
    }
  };

  const updatePreference = (notificationType, channel, enabled) => {
    setPreferences(prev => ({
      ...prev,
      [notificationType]: {
        ...prev[notificationType],
        [channel]: enabled
      }
    }));
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      await notificationService.updateNotificationPreferences(preferences);
      toast.success('Préférences sauvegardées avec succès');
    } catch (error) {
      console.error('Failed to save preferences:', error);
      toast.error('Erreur lors de la sauvegarde des préférences');
    } finally {
      setSaving(false);
    }
  };

  const toggleAll = (channel, enabled) => {
    const updatedPreferences = { ...preferences };
    
    notificationTypes.forEach(category => {
      category.types.forEach(type => {
        if (!updatedPreferences[type.key]) {
          updatedPreferences[type.key] = {
            in_app_enabled: true,
            email_enabled: false,
            discord_dm_enabled: false
          };
        }
        updatedPreferences[type.key][channel] = enabled;
      });
    });
    
    setPreferences(updatedPreferences);
  };

  const getPreferenceValue = (notificationType, channel) => {
    return preferences[notificationType]?.[channel] || false;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-dark-800 transition-colors duration-200"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <h1 className="text-3xl font-bold text-white">Préférences de notifications</h1>
          </div>
          <p className="text-gray-400">
            Configurez comment et quand vous souhaitez recevoir des notifications
          </p>
        </div>

        {/* Actions */}
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Actions rapides</h3>
              <p className="text-gray-400 text-sm">Activez ou désactivez toutes les notifications par canal</p>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => toggleAll('in_app_enabled', true)}
                className="inline-flex items-center px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                <CheckIcon className="w-4 h-4 mr-2" />
                Tout activer (App)
              </button>
              <button
                onClick={() => toggleAll('in_app_enabled', false)}
                className="inline-flex items-center px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
              >
                <XMarkIcon className="w-4 h-4 mr-2" />
                Tout désactiver (App)
              </button>
              <button
                onClick={() => toggleAll('email_enabled', true)}
                className="inline-flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                <CheckIcon className="w-4 h-4 mr-2" />
                Tout activer (Email)
              </button>
              <button
                onClick={() => toggleAll('email_enabled', false)}
                className="inline-flex items-center px-3 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200"
              >
                <XMarkIcon className="w-4 h-4 mr-2" />
                Tout désactiver (Email)
              </button>
            </div>
          </div>
        </div>

        {/* Preferences Table */}
        <div className="bg-dark-800 rounded-lg border border-dark-700 overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-dark-700">
            <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-400">
              <div className="col-span-6">Type de notification</div>
              <div className="col-span-2 text-center">
                <div className="flex items-center justify-center">
                  <BellIcon className="w-4 h-4 mr-1" />
                  App
                </div>
              </div>
              <div className="col-span-2 text-center">
                <div className="flex items-center justify-center">
                  <EnvelopeIcon className="w-4 h-4 mr-1" />
                  Email
                </div>
              </div>
              <div className="col-span-2 text-center">
                <div className="flex items-center justify-center">
                  💬 Discord
                </div>
              </div>
            </div>
          </div>

          <div className="divide-y divide-dark-700">
            {notificationTypes.map((category, categoryIndex) => (
              <div key={categoryIndex}>
                {/* Category Header */}
                <div className="px-6 py-3 bg-dark-750">
                  <h4 className="text-sm font-semibold text-primary-400 uppercase tracking-wide">
                    {category.category}
                  </h4>
                </div>

                {/* Category Items */}
                {category.types.map((type, typeIndex) => (
                  <div key={type.key} className="px-6 py-4 hover:bg-dark-750 transition-colors duration-200">
                    <div className="grid grid-cols-12 gap-4 items-center">
                      <div className="col-span-6">
                        <div>
                          <h5 className="text-white font-medium">{type.label}</h5>
                          <p className="text-gray-400 text-sm mt-1">{type.description}</p>
                        </div>
                      </div>
                      
                      {/* In-app toggle */}
                      <div className="col-span-2 text-center">
                        <label className="inline-flex items-center">
                          <input
                            type="checkbox"
                            checked={getPreferenceValue(type.key, 'in_app_enabled')}
                            onChange={(e) => updatePreference(type.key, 'in_app_enabled', e.target.checked)}
                            className="form-checkbox h-5 w-5 text-primary-600 rounded focus:ring-primary-500 focus:ring-offset-0"
                          />
                        </label>
                      </div>
                      
                      {/* Email toggle */}
                      <div className="col-span-2 text-center">
                        <label className="inline-flex items-center">
                          <input
                            type="checkbox"
                            checked={getPreferenceValue(type.key, 'email_enabled')}
                            onChange={(e) => updatePreference(type.key, 'email_enabled', e.target.checked)}
                            className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500 focus:ring-offset-0"
                          />
                        </label>
                      </div>
                      
                      {/* Discord DM toggle */}
                      <div className="col-span-2 text-center">
                        <label className="inline-flex items-center">
                          <input
                            type="checkbox"
                            checked={getPreferenceValue(type.key, 'discord_dm_enabled')}
                            onChange={(e) => updatePreference(type.key, 'discord_dm_enabled', e.target.checked)}
                            className="form-checkbox h-5 w-5 text-purple-600 rounded focus:ring-purple-500 focus:ring-offset-0"
                            disabled={true}
                            title="Discord DM sera disponible prochainement"
                          />
                        </label>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between bg-dark-800 rounded-lg p-6 border border-dark-700">
          <div>
            <p className="text-gray-400 text-sm">
              💡 Les notifications Discord DM seront disponibles prochainement avec l'intégration du bot Discord.
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              to="/notifications"
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors duration-200"
            >
              Annuler
            </Link>
            <button
              onClick={savePreferences}
              disabled={saving}
              className="inline-flex items-center px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {saving ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2"></div>
                  Sauvegarde...
                </>
              ) : (
                <>
                  <CheckIcon className="w-4 h-4 mr-2" />
                  Sauvegarder
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationPreferencesPage;