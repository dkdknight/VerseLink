import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { eventService } from '../services/eventService';

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
    banner_url: ''
  });
  const [roles, setRoles] = useState([]);
  const [orgVisibility, setOrgVisibility] = useState('all');
  const [allowedOrgs, setAllowedOrgs] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
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
    try {
      setLoading(true);
      const startUtc = new Date(formData.start_at_utc).toISOString();
      const allowedOrgIds =
        orgVisibility === 'selected'
          ? allowedOrgs.split(',').map(id => id.trim()).filter(Boolean)
          : [];

      const payload = {
        ...formData,
        type: formData.type.trim().toLowerCase(),
        duration_minutes: parseInt(formData.duration_minutes, 10),
        max_participants: formData.max_participants ? parseInt(formData.max_participants, 10) : null,
        start_at_utc: startUtc,
        roles: roles.map(r => ({
          name: r.name,
          capacity: parseInt(r.capacity, 10),
          description: r.description
        })),
        allowed_org_ids: allowedOrgIds,
        banner_url: formData.banner_url || null
      };
      await eventService.createEvent(id, payload);
      toast.success('Événement créé');
      navigate('/events');
    } catch (error) {
      console.error('Failed to create event:', error);
      const message = error.response?.data?.detail || "Erreur lors de la création de l'événement";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
          <h1 className="text-2xl font-bold text-white mb-6">Créer un événement</h1>
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