import React, { useState } from 'react';
import { 
  XMarkIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { tournamentService } from '../services/tournamentService';

const MatchDisputeModal = ({ isOpen, onClose, match, onDisputeCreated }) => {
  const [disputeReason, setDisputeReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmitDispute = async (e) => {
    e.preventDefault();
    
    if (!disputeReason.trim() || disputeReason.trim().length < 10) {
      toast.error('La raison de la dispute doit contenir au moins 10 caractères');
      return;
    }

    try {
      setSubmitting(true);
      await tournamentService.createMatchDispute(match.id, {
        dispute_reason: disputeReason.trim()
      });
      
      toast.success('Dispute créée avec succès !');
      onDisputeCreated();
      onClose();
      
      // Reset form
      setDisputeReason('');
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la création de la dispute');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      setDisputeReason('');
      onClose();
    }
  };

  if (!isOpen || !match) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-red-500/30">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-600">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-400" />
            <h2 className="text-xl font-semibold text-white">Contester le résultat</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={submitting}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmitDispute} className="p-6 space-y-6">
          {/* Match Info */}
          <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
            <h3 className="text-lg font-medium text-white mb-3">Informations du match</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-3">
              <div className="text-center">
                <h4 className="font-medium text-white">{match.team_a_name || 'TBD'}</h4>
                <p className="text-sm text-gray-400">Équipe A</p>
                {match.score_a !== null && (
                  <p className="text-2xl font-bold text-white mt-1">{match.score_a}</p>
                )}
              </div>
              <div className="text-center">
                <h4 className="font-medium text-white">{match.team_b_name || 'TBD'}</h4>
                <p className="text-sm text-gray-400">Équipe B</p>
                {match.score_b !== null && (
                  <p className="text-2xl font-bold text-white mt-1">{match.score_b}</p>
                )}
              </div>
            </div>
            
            <div className="text-center text-sm text-gray-400">
              Round {match.round} • État: {match.state}
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mr-2 mt-0.5" />
              <div className="text-yellow-300 text-sm">
                <p className="font-medium mb-1">Important :</p>
                <ul className="text-xs space-y-1">
                  <li>• Les disputes doivent être fondées sur des preuves valides</li>
                  <li>• Les disputes frivoles peuvent entraîner des sanctions</li>
                  <li>• Un administrateur examinera votre demande</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Dispute Reason */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Raison de la dispute *
            </label>
            <textarea
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              placeholder="Expliquez en détail pourquoi vous contestez ce résultat. Incluez toute preuve ou information pertinente..."
              rows={6}
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
              required
              minLength={10}
              maxLength={1000}
              disabled={submitting}
            />
            <div className="flex justify-between mt-1">
              <p className="text-xs text-gray-400">
                Minimum 10 caractères requis
              </p>
              <p className="text-xs text-gray-400">
                {disputeReason.length}/1000 caractères
              </p>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-dark-600">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary"
              disabled={submitting}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={submitting || !disputeReason.trim() || disputeReason.trim().length < 10}
              className="btn-danger flex items-center"
            >
              {submitting ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2"></div>
                  Envoi...
                </>
              ) : (
                <>
                  <DocumentTextIcon className="w-4 h-4 mr-2" />
                  Créer la dispute
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MatchDisputeModal;