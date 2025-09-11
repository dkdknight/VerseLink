import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { organizationService } from '../services/organizationService';

const CreateOrganizationPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    tag: '',
    description: '',
    website_url: '',
    discord_url: '',
    twitter_url: '',
    youtube_url: '',
    twitch_url: '',
    visibility: 'public',
    membership_policy: 'open',
    logo_url: '',
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
      const org = await organizationService.createOrganization(formData);
      toast.success("Organisation créée");
      navigate(`/organizations/${org.id}`);
    } catch (error) {
      console.error('Failed to create organization:', error);
      const message = error.response?.data?.detail || "Erreur lors de la création de l'organisation";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
          <h1 className="text-2xl font-bold text-white mb-6">Créer une organisation</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
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
              <label className="block text-gray-300 mb-1">Tag</label>
              <input
                type="text"
                name="tag"
                value={formData.tag}
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
              ></textarea>
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Site web</label>
              <input
                type="text"
                name="website_url"
                value={formData.website_url}
                onChange={handleChange}
                className="input-primary w-full"
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-1">Visibilité</label>
              <select
                name="visibility"
                value={formData.visibility}
                onChange={handleChange}
                className="input-primary w-full"
              >
                <option value="public">Publique</option>
                <option value="unlisted">Non listée</option>
                <option value="private">Privée</option>
              </select>
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

export default CreateOrganizationPage;