import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { eventService } from '../services/eventService';
import { discordService } from '../services/discordService';

const CreateEventPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'autre',
    start_at_utc: '',
    duration_minutes: 60,
    location: '',
    max_participants: '',
    banner_url: '',
    discord_integration_enabled: true
  });
  const [roles, setRoles] = useState([]);
  const [orgVisibility, setOrgVisibility] = useState('all');
  const [allowedOrgs, setAllowedOrgs] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleRoleChange = (index, e) => {
    const { name, value } = e.target;
    setRoles(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [name]: value };
      return updated;
    });
  };

  const addRole = () => {
    setRoles(prev => [...prev, { name: '', capacity: 1, description: '' }]);
  };

  const removeRole = (index) => {
    setRoles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    try {
      setLoading(true);
      const startDate = new Date(formData.start_at_utc);
      if (isNaN(startDate.getTime())) {
        toast.error('Date de début invalide');
        setLoading(false);
        return;
      }
      if (startDate <= new Date()) {
        toast.error('La date doit être dans le futur');
        setLoading(false);
        return;
      }
      const duration = parseInt(formData.duration_minutes, 10);
      if (isNaN(duration) || duration <= 0) {
        toast.error('La durée doit être un entier positif');
        setLoading(false);
        return;
      }
      const allowedOrgIds =
        orgVisibility === 'selected'
          ? allowedOrgs.split(',').map(id => id.trim()).filter(Boolean)
          : [];

      const payload = {
        title: formData.title,
        description: formData.description,
        type: formData.type.trim().toLowerCase(),
        start_at_utc: startDate.toISOString(),
        duration_minutes: duration,
        location: formData.location || null,
        max_participants: formData.max_participants ? parseInt(formData.max_participants, 10) : null,
        banner_url: formData.banner_url || null,
        discord_integration_enabled: formData.discord_integration_enabled,
        roles: roles.map(r => ({
          name: r.name,
          capacity: parseInt(r.capacity, 10),
          description: r.description
        })),
        allowed_org_ids: allowedOrgIds
      };
      const result = await eventService.createEvent(id, payload);
      
      // Publier automatiquement sur Discord si possible
      let discordPublished = false;
      let discordError = null;
      
      try {
        const discordResult = await discordService.publishEvent(payload, id);
        if (discordResult.success) {
          discordPublished = true;
        }
      } catch (discordErr) {
        discordError = discordErr;
        console.warn('Failed to publish to Discord:', discordErr);
        // Ne pas faire échouer la création pour ça
      }

      // Toast selon le résultat
      if (discordPublished) {
        toast.success('🎉 Événement créé et publié sur Discord !');
      } else if (discordError) {
        toast.success('✅ Événement créé !');
        toast('💬 Publication Discord non disponible', { icon: 'ℹ️' });
      } else {
        toast.success('✅ Événement créé avec succès !');
      }
      if (result?.event_id) {
        try {
          await eventService.startEvent(result.event_id);
        } catch (err) {
          console.error('Failed to start event:', err);
        }
      }
      navigate('/events');
    } catch (error) {
      console.error('Failed to create event:', error);
      let message = "Erreur lors de la création de l'événement";
      
      if (error.response) {
        console.log('Error response:', error.response);
        if (error.response.status === 422) {
          // Validation errors
          const validationError = error.response.data;
          if (validationError && validationError.detail && Array.isArray(validationError.detail)) {
            const errorMessages = validationError.detail.map(err => {
              if (err.loc && err.msg) {
                const field = err.loc[err.loc.length - 1];
                return `${field}: ${err.msg}`;
              }
              return err.msg || 'Erreur de validation';
            });
            message = `Erreurs de validation:\n${errorMessages.join('\n')}`;
          } else if (validationError && validationError.detail) {
            message = validationError.detail;
          }
        } else if (error.response.status === 401) {
          message = "Erreur d'authentification. Veuillez vous reconnecter.";
        } else if (error.response.status === 403) {
          message = "Permissions insuffisantes pour créer un événement dans cette organisation.";
        } else {
          try {
            const data = typeof error.response.data === 'string' 
              ? JSON.parse(error.response.data) 
              : error.response.data;
            message = data?.detail || message;
          } catch (parseErr) {
            message = error.response.data?.detail || `Erreur ${error.response.status}: ${error.response.statusText}`;
          }
        }
      } else if (error.message) {
        message = error.message;
      }
      
      setErrorMessage(message);
      toast.error(message.split('\n')[0]); // Show first line in toast
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
          <h1 className="text-2xl font-bold text-white mb-6">Créer un événement</h1>
          {errorMessage && (
            <div className="mb-4 p-4 bg-red-900/20 border border-red-500 rounded-lg">
              <h4 className="text-red-400 font-semibold mb-2">Erreur</h4>
              <div className="text-red-300 text-sm whitespace-pre-line">{errorMessage}</div>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-gray-300 mb-1">Titre</label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="input-primary w-full"
                required
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                className="input-primary w-full"
                rows="3"
                required
              ></textarea>
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Type</label>
              <select
                name="type"
                value={formData.type}
                onChange={handleChange}
                className="input-primary w-full"
              >
                <option value="raid">Raid</option>
                <option value="course">Course</option>
                <option value="pvp">PvP</option>
                <option value="fps">FPS</option>
                <option value="salvaging">Salvaging</option>
                <option value="logistique">Logistique</option>
                <option value="exploration">Exploration</option>
                <option value="mining">Mining</option>
                <option value="trading">Trading</option>
                <option value="roleplay">Roleplay</option>
                <option value="autre">Autre</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Début</label>
              <input
                type="datetime-local"
                name="start_at_utc"
                value={formData.start_at_utc}
                onChange={handleChange}
                className="input-primary w-full"
                required
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Durée (minutes)</label>
              <input
                type="number"
                name="duration_minutes"
                value={formData.duration_minutes}
                onChange={handleChange}
                className="input-primary w-full"
                required
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Lieu</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="input-primary w-full"
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Participants max</label>
              <input
                type="number"
                name="max_participants"
                value={formData.max_participants}
                onChange={handleChange}
                className="input-primary w-full"
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Image (URL)</label>
              <input
                type="text"
                name="banner_url"
                value={formData.banner_url}
                onChange={handleChange}
                className="input-primary w-full"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                name="discord_integration_enabled"
                checked={formData.discord_integration_enabled}
                onChange={handleChange}
                className=""
              />
              <span className="text-gray-300">Annoncer sur Discord</span>
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Rôles</label>
              {roles.map((role, index) => (
                <div key={index} className="mb-2 p-3 border border-dark-700 rounded">
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      name="name"
                      placeholder="Nom"
                      value={role.name}
                      onChange={(e) => handleRoleChange(index, e)}
                      className="input-primary flex-1"
                    />
                    <input
                      type="number"
                      name="capacity"
                      placeholder="Capacité"
                      value={role.capacity}
                      onChange={(e) => handleRoleChange(index, e)}
                      className="input-primary w-24"
                    />
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      name="description"
                      placeholder="Description"
                      value={role.description}
                      onChange={(e) => handleRoleChange(index, e)}
                      className="input-primary flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => removeRole(index)}
                      className="btn-secondary"
                    >
                      Retirer
                    </button>
                  </div>
                </div>
              ))}
              <button
                type="button"
                onClick={addRole}
                className="btn-secondary mt-2"
              >
                Ajouter un rôle
              </button>
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Visibilité</label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="orgVisibility"
                    value="all"
                    checked={orgVisibility === 'all'}
                    onChange={(e) => setOrgVisibility(e.target.value)}
                    className="mr-2"
                  />
                  <span>Accessible à toutes les organisations</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="orgVisibility"
                    value="selected"
                    checked={orgVisibility === 'selected'}
                    onChange={(e) => setOrgVisibility(e.target.value)}
                    className="mr-2"
                  />
                  <span>Uniquement aux organisations sélectionnées</span>
                </label>
              </div>
              {orgVisibility === 'selected' && (
                <input
                  type="text"
                  value={allowedOrgs}
                  onChange={(e) => setAllowedOrgs(e.target.value)}
                  placeholder="IDs des organisations séparés par des virgules"
                  className="input-primary w-full mt-2"
                />
              )}
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Création...' : 'Créer'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateEventPage;