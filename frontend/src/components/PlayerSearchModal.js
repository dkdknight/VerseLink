import React, { useState, useEffect } from 'react';
import { 
  XMarkIcon,
  MagnifyingGlassIcon,
  UserPlusIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const PlayerSearchModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isLoading, 
  tournament, 
  initialData = null, 
  isEdit = false 
}) => {
  const [formData, setFormData] = useState({
    preferred_role: '',
    experience_level: '',
    description: ''
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        preferred_role: initialData.preferred_role || '',
        experience_level: initialData.experience_level || '',
        description: initialData.description || ''
      });
    }
  }, [initialData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate that at least one field is filled
    if (!formData.preferred_role.trim() && !formData.experience_level.trim() && !formData.description.trim()) {
      toast.error('Veuillez remplir au moins un champ');
      return;
    }

    await onSubmit(formData);
    handleClose();
  };

  const handleClose = () => {
    if (!isLoading) {
      setFormData({
        preferred_role: '',
        experience_level: '',
        description: ''
      });
      onClose();
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-dark-600">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-600">
          <div className="flex items-center space-x-3">
            <MagnifyingGlassIcon className="w-6 h-6 text-primary-400" />
            <h2 className="text-xl font-semibold text-white">
              {isEdit ? 'Modifier ma recherche' : 'Créer ma recherche d\'équipiers'}
            </h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isLoading}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Tournament Info */}
          <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
            <h3 className="text-lg font-medium text-white mb-2">Tournoi</h3>
            <p className="text-gray-300">{tournament.name}</p>
            <p className="text-sm text-gray-400 mt-1">
              {tournament.team_size} joueurs par équipe • {tournament.format}
            </p>
          </div>

          {/* Help Text */}
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
            <div className="flex items-start">
              <UserPlusIcon className="w-5 h-5 text-blue-400 mr-2 mt-0.5" />
              <div className="text-blue-300 text-sm">
                <p className="font-medium mb-1">Conseils pour une recherche efficace :</p>
                <ul className="text-xs space-y-1">
                  <li>• Précisez votre rôle préféré (pilote, gunner, support, etc.)</li>
                  <li>• Indiquez votre niveau d'expérience honnêtement</li>
                  <li>• Décrivez vos disponibilités et votre style de jeu</li>
                  <li>• Mentionnez vos équipements ou spécialisations</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            {/* Preferred Role */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Rôle préféré
              </label>
              <input
                type="text"
                value={formData.preferred_role}
                onChange={(e) => handleInputChange('preferred_role', e.target.value)}
                placeholder="Ex: Pilote, Gunner, Engineer, Support..."
                className="input-primary w-full"
                maxLength={100}
                disabled={isLoading}
              />
              <p className="text-xs text-gray-400 mt-1">
                Quel rôle préférez-vous jouer dans une équipe ? (optionnel)
              </p>
            </div>

            {/* Experience Level */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Niveau d'expérience
              </label>
              <input
                type="text"
                value={formData.experience_level}
                onChange={(e) => handleInputChange('experience_level', e.target.value)}
                placeholder="Ex: Débutant, Intermédiaire, Expert, Vétéran..."
                className="input-primary w-full"
                maxLength={50}
                disabled={isLoading}
              />
              <p className="text-xs text-gray-400 mt-1">
                Quel est votre niveau d'expérience dans Star Citizen ? (optionnel)
              </p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description personnelle
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Parlez de vous, vos disponibilités, votre style de jeu, vos équipements, ce que vous recherchez dans une équipe..."
                rows={4}
                className="input-primary w-full resize-none"
                maxLength={500}
                disabled={isLoading}
              />
              <div className="flex justify-between mt-1">
                <p className="text-xs text-gray-400">
                  Présentez-vous aux capitaines d'équipe (optionnel)
                </p>
                <p className="text-xs text-gray-400">
                  {formData.description.length}/500 caractères
                </p>
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
            <div className="flex items-start">
              <MagnifyingGlassIcon className="w-5 h-5 text-yellow-400 mr-2 mt-0.5" />
              <div className="text-yellow-300 text-sm">
                <p className="font-medium mb-1">Important :</p>
                <ul className="text-xs space-y-1">
                  <li>• Votre recherche sera visible par tous les capitaines d'équipe</li>
                  <li>• Elle sera automatiquement désactivée si vous rejoignez une équipe</li>
                  <li>• Vous pouvez la modifier ou la désactiver à tout moment</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-dark-600">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary"
              disabled={isLoading}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary flex items-center"
            >
              {isLoading ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2"></div>
                  {isEdit ? 'Mise à jour...' : 'Création...'}
                </>
              ) : (
                <>
                  <UserPlusIcon className="w-4 h-4 mr-2" />
                  {isEdit ? 'Mettre à jour' : 'Créer ma recherche'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PlayerSearchModal;