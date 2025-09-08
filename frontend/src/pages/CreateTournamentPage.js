import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { tournamentService } from '../services/tournamentService';

const CreateTournamentPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    org_id: '',
    name: '',
    description: '',
    format: 'se',
    start_at_utc: '',
    max_teams: 8,
    team_size: 5,
    prize_pool: '',
    banner_url: ''
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
      const startUtc = new Date(formData.start_at_utc).toISOString();
      const payload = {
        name: formData.name,
        description: formData.description,
        format: formData.format,
        start_at_utc: startUtc,
        max_teams: parseInt(formData.max_teams, 10),
        team_size: parseInt(formData.team_size, 10),
        prize_pool: formData.prize_pool || null,
        banner_url: formData.banner_url || null
      };
      await tournamentService.createTournament(formData.org_id, payload);
      toast.success('Tournoi créé');
      navigate('/tournaments');
    } catch (error) {
      console.error('Failed to create tournament:', error);
      const message = error.response?.data?.detail || "Erreur lors de la création du tournoi";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
          <h1 className="text-2xl font-bold text-white mb-6">Créer un tournoi</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-gray-300 mb-1">ID de l'organisation</label>
              <input
                type="text"
                name="org_id"
                value={formData.org_id}
                onChange={handleChange}
                className="input-primary w-full"
                required
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Nom</label>
              <input
                type="text"
                name="name"
                value={formData.name}
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
              <label className="block text-gray-300 mb-1">Format</label>
              <select
                name="format"
                value={formData.format}
                onChange={handleChange}
                className="input-primary w-full"
              >
                <option value="se">Simple Élimination</option>
                <option value="de">Double Élimination</option>
                <option value="rr">Round Robin</option>
                <option value="swiss">Système Suisse</option>
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
              <label className="block text-gray-300 mb-1">Nombre maximum d'équipes</label>
              <input
                type="number"
                name="max_teams"
                value={formData.max_teams}
                onChange={handleChange}
                className="input-primary w-full"
                required
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Taille des équipes</label>
              <input
                type="number"
                name="team_size"
                value={formData.team_size}
                onChange={handleChange}
                className="input-primary w-full"
                required
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Récompense (facultatif)</label>
              <input
                type="text"
                name="prize_pool"
                value={formData.prize_pool}
                onChange={handleChange}
                className="input-primary w-full"
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Bannière (URL facultative)</label>
              <input
                type="text"
                name="banner_url"
                value={formData.banner_url}
                onChange={handleChange}
                className="input-primary w-full"
              />
            </div>
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Création...' : 'Créer le tournoi'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateTournamentPage;