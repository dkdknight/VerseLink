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
    max_participants: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const startUtc = new Date(formData.start_at_utc)
        .toISOString()
        .slice(0, 19); // remove timezone to keep backend comparison compatible

      const payload = {
        ...formData,
        duration_minutes: parseInt(formData.duration_minutes, 10),
        max_participants: formData.max_participants ? parseInt(formData.max_participants, 10) : null,
        start_at_utc: startUtc
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