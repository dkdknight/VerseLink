import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../App';
import { 
  PencilIcon, 
  CheckIcon, 
  XMarkIcon,
  UserCircleIcon,
  StarIcon,
  TrophyIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';

const ProfilePage = () => {
  const { user, updateProfile } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    handle: '',
    bio: '',
    timezone: 'UTC',
    locale: 'fr',
    dm_opt_in: false
  });

  useEffect(() => {
    if (user) {
      setFormData({
        handle: user.handle || '',
        bio: user.bio || '',
        timezone: user.timezone || 'UTC',
        locale: user.locale || 'fr',
        dm_opt_in: user.dm_opt_in || false
      });
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      
      // Only send changed fields
      const changes = {};
      Object.keys(formData).forEach(key => {
        if (formData[key] !== user[key]) {
          changes[key] = formData[key];
        }
      });

      if (Object.keys(changes).length === 0) {
        setEditing(false);
        return;
      }

      await updateProfile(changes);
      toast.success('Profil mis à jour avec succès');
      setEditing(false);
    } catch (error) {
      console.error('Profile update failed:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la mise à jour du profil');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset form data
    setFormData({
      handle: user.handle || '',
      bio: user.bio || '',
      timezone: user.timezone || 'UTC',
      locale: user.locale || 'fr',
      dm_opt_in: user.dm_opt_in || false
    });
    setEditing(false);
  };

  const timezones = [
    'UTC',
    'Europe/Paris',
    'Europe/London',
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Asia/Tokyo',
    'Australia/Sydney'
  ];

  if (!user) {
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
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 text-shadow">
            Profil Utilisateur
          </h1>
          <p className="text-gray-400">
            Gérez vos informations personnelles et préférences
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <div className="card p-6 text-center">
              {/* Avatar */}
              <div className="mb-6">
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.handle}
                    className="w-24 h-24 rounded-full mx-auto border-4 border-primary-400 glow-primary"
                  />
                ) : (
                  <UserCircleIcon className="w-24 h-24 text-gray-400 mx-auto" />
                )}
              </div>

              {/* Basic Info */}
              <h2 className="text-2xl font-bold text-white mb-2">{user.handle}</h2>
              <p className="text-gray-400 mb-4">{user.discord_username}</p>
              
              {/* Badges */}
              <div className="flex flex-wrap gap-2 justify-center mb-6">
                {user.roles?.map((role) => (
                  <span 
                    key={role}
                    className="px-3 py-1 bg-primary-600 text-white text-xs rounded-full font-medium"
                  >
                    {role}
                  </span>
                ))}
                {user.is_verified && (
                  <span className="px-3 py-1 bg-accent-green text-white text-xs rounded-full font-medium">
                    Vérifié
                  </span>
                )}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="glass-effect rounded-lg p-3">
                  <StarIcon className="w-6 h-6 text-accent-gold mx-auto mb-1" />
                  <div className="text-lg font-bold text-white">{user.reputation}</div>
                  <div className="text-xs text-gray-400">Réputation</div>
                </div>
                <div className="glass-effect rounded-lg p-3">
                  <TrophyIcon className="w-6 h-6 text-primary-400 mx-auto mb-1" />
                  <div className="text-lg font-bold text-white">0</div>
                  <div className="text-xs text-gray-400">Tournois</div>
                </div>
              </div>
            </div>
          </div>

          {/* Profile Form */}
          <div className="lg:col-span-2">
            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-white">Informations Personnelles</h3>
                {!editing ? (
                  <button
                    onClick={() => setEditing(true)}
                    className="btn-secondary flex items-center"
                  >
                    <PencilIcon className="w-4 h-4 mr-2" />
                    Modifier
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSave}
                      disabled={loading}
                      className="btn-primary flex items-center"
                    >
                      <CheckIcon className="w-4 h-4 mr-2" />
                      {loading ? 'Enregistrement...' : 'Enregistrer'}
                    </button>
                    <button
                      onClick={handleCancel}
                      disabled={loading}
                      className="btn-ghost flex items-center"
                    >
                      <XMarkIcon className="w-4 h-4 mr-2" />
                      Annuler
                    </button>
                  </div>
                )}
              </div>

              <div className="space-y-6">
                {/* Handle */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Pseudo
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      name="handle"
                      value={formData.handle}
                      onChange={handleInputChange}
                      className="input-primary w-full"
                      placeholder="Votre pseudo unique"
                      minLength={3}
                      maxLength={32}
                    />
                  ) : (
                    <div className="input-primary bg-dark-700">{user.handle}</div>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    3-32 caractères, lettres, chiffres, tirets et underscores uniquement
                  </p>
                </div>

                {/* Bio */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Bio
                  </label>
                  {editing ? (
                    <textarea
                      name="bio"
                      value={formData.bio}
                      onChange={handleInputChange}
                      rows={4}
                      className="input-primary w-full resize-none"
                      placeholder="Parlez-nous de vous..."
                      maxLength={500}
                    />
                  ) : (
                    <div className="input-primary bg-dark-700 min-h-[100px]">
                      {user.bio || "Aucune bio renseignée"}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Maximum 500 caractères
                  </p>
                </div>

                {/* Timezone */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Fuseau horaire
                  </label>
                  {editing ? (
                    <select
                      name="timezone"
                      value={formData.timezone}
                      onChange={handleInputChange}
                      className="input-primary w-full"
                    >
                      {timezones.map(tz => (
                        <option key={tz} value={tz}>{tz}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="input-primary bg-dark-700">{user.timezone}</div>
                  )}
                </div>

                {/* Language */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Langue
                  </label>
                  {editing ? (
                    <select
                      name="locale"
                      value={formData.locale}
                      onChange={handleInputChange}
                      className="input-primary w-full"
                    >
                      <option value="fr">Français</option>
                      <option value="en">English</option>
                    </select>
                  ) : (
                    <div className="input-primary bg-dark-700">
                      {user.locale === 'fr' ? 'Français' : 'English'}
                    </div>
                  )}
                </div>

                {/* DM Opt-in */}
                <div className="flex items-center">
                  {editing ? (
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        name="dm_opt_in"
                        checked={formData.dm_opt_in}
                        onChange={handleInputChange}
                        className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
                      />
                      <span className="ml-3 text-gray-300">
                        Autoriser les messages privés via Discord
                      </span>
                    </label>
                  ) : (
                    <div className="flex items-center">
                      <div className={`w-4 h-4 rounded ${user.dm_opt_in ? 'bg-primary-600' : 'bg-dark-600'} mr-3`}>
                        {user.dm_opt_in && <CheckIcon className="w-3 h-3 text-white" />}
                      </div>
                      <span className="text-gray-300">
                        Messages privés Discord : {user.dm_opt_in ? 'Autorisés' : 'Désactivés'}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Account Info */}
              <div className="mt-8 pt-6 border-t border-dark-600">
                <h4 className="text-lg font-semibold text-white mb-4">Informations du compte</h4>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Membre depuis :</span>
                    <div className="text-white">
                      {new Date(user.created_at).toLocaleDateString('fr-FR')}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Dernière connexion :</span>
                    <div className="text-white">
                      {user.last_seen_at 
                        ? new Date(user.last_seen_at).toLocaleDateString('fr-FR')
                        : 'Jamais'
                      }
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;