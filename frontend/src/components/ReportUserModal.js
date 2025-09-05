import React, { useState } from 'react';
import { 
  XMarkIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { moderationService } from '../services/moderationService';

const ReportUserModal = ({ isOpen, onClose, reportedUser }) => {
  const [formData, setFormData] = useState({
    type: '',
    reason: '',
    context_url: '',
    additional_info: {}
  });
  const [submitting, setSubmitting] = useState(false);

  const reportTypes = [
    { value: 'spam', label: 'Spam', description: 'Messages répétitifs ou non sollicités' },
    { value: 'harassment', label: 'Harcèlement', description: 'Comportement abusif ou intimidant' },
    { value: 'inappropriate_content', label: 'Contenu inapproprié', description: 'Contenu offensant ou inapproprié' },
    { value: 'cheating', label: 'Triche', description: 'Utilisation de triche ou comportement déloyal' },
    { value: 'no_show', label: 'Absence non justifiée', description: 'Ne s\'est pas présenté à un événement sans prévenir' },
    { value: 'griefing', label: 'Griefing', description: 'Comportement intentionnellement perturbateur' },
    { value: 'other', label: 'Autre', description: 'Autre raison non listée ci-dessus' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.type || !formData.reason.trim()) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    if (formData.reason.trim().length < 10) {
      toast.error('La raison doit contenir au moins 10 caractères');
      return;
    }

    try {
      setSubmitting(true);
      await moderationService.createReport({
        reported_user_id: reportedUser.id,
        type: formData.type,
        reason: formData.reason.trim(),
        context_url: formData.context_url.trim() || null,
        additional_info: formData.additional_info
      });
      
      toast.success('Signalement envoyé avec succès');
      onClose();
      
      // Reset form
      setFormData({
        type: '',
        reason: '',
        context_url: '',
        additional_info: {}
      });
    } catch (error) {
      console.error('Failed to submit report:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de l\'envoi du signalement');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto border border-dark-600">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-600">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-orange-400" />
            <h2 className="text-xl font-semibold text-white">Signaler un utilisateur</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* User Info */}
          <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
            <p className="text-sm text-gray-400 mb-2">Utilisateur signalé :</p>
            <div className="flex items-center space-x-3">
              {reportedUser?.avatar_url ? (
                <img
                  src={reportedUser.avatar_url}
                  alt={reportedUser.handle}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {reportedUser?.handle?.charAt(0)?.toUpperCase()}
                  </span>
                </div>
              )}
              <span className="text-white font-medium">{reportedUser?.handle}</span>
            </div>
          </div>

          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Type de signalement *
            </label>
            <select
              value={formData.type}
              onChange={(e) => handleChange('type', e.target.value)}
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            >
              <option value="">Sélectionnez un type</option>
              {reportTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            {formData.type && (
              <p className="text-xs text-gray-400 mt-1">
                {reportTypes.find(t => t.value === formData.type)?.description}
              </p>
            )}
          </div>

          {/* Reason */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Raison détaillée * (minimum 10 caractères)
            </label>
            <textarea
              value={formData.reason}
              onChange={(e) => handleChange('reason', e.target.value)}
              placeholder="Décrivez en détail le comportement problématique..."
              rows={4}
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              required
              minLength={10}
              maxLength={1000}
            />
            <p className="text-xs text-gray-400 mt-1">
              {formData.reason.length}/1000 caractères
            </p>
          </div>

          {/* Context URL */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              URL du contexte (optionnel)
            </label>
            <input
              type="url"
              value={formData.context_url}
              onChange={(e) => handleChange('context_url', e.target.value)}
              placeholder="https://exemple.com/page-ou-incident-a-eu-lieu"
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-400 mt-1">
              URL de la page où l'incident a eu lieu (événement, tournoi, etc.)
            </p>
          </div>

          {/* Warning */}
          <div className="bg-orange-900/20 border border-orange-500/30 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-orange-300">
                <p className="font-medium mb-1">Avertissement</p>
                <p>
                  Les faux signalements sont contraires aux règles de la plateforme. 
                  Assurez-vous que votre signalement est légitime et étayé par des faits.
                </p>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-dark-600">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors duration-200"
              disabled={submitting}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={submitting || !formData.type || !formData.reason.trim() || formData.reason.length < 10}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {submitting ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2 inline-block"></div>
                  Envoi...
                </>
              ) : (
                'Envoyer le signalement'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ReportUserModal;