import React from 'react';
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { tournamentService } from '../services/tournamentService';

const MatchConfirmModal = ({ isOpen, onClose, match, onConfirmed, onContest }) => {
  const [submitting, setSubmitting] = React.useState(false);

  const handleConfirm = async () => {
    try {
      setSubmitting(true);
      await tournamentService.confirmMatchScore(match.id);
      toast.success('Score validé');
      onConfirmed();
      onClose();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("Erreur lors de la validation du score");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleContest = () => {
    if (onContest) {
      onContest();
    }
  };

  if (!isOpen || !match) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-lg w-full border border-dark-600">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-600">
          <div className="flex items-center space-x-3">
            <CheckCircleIcon className="w-6 h-6 text-green-400" />
            <h2 className="text-xl font-semibold text-white">Confirmer le score</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Match Info */}
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <h4 className="text-white font-medium">{match.team_a_name || 'TBD'}</h4>
              {match.score_a !== null && (
                <p className="text-2xl font-bold text-white mt-1">{match.score_a}</p>
              )}
            </div>
            <div className="text-center">
              <h4 className="text-white font-medium">{match.team_b_name || 'TBD'}</h4>
              {match.score_b !== null && (
                <p className="text-2xl font-bold text-white mt-1">{match.score_b}</p>
              )}
            </div>
          </div>
          <p className="text-sm text-gray-400 text-center">
            Confirmez-vous ce résultat ?
          </p>
          <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3 flex items-start">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mr-2" />
            <p className="text-yellow-300 text-xs">
              En cas de contestation, vous devrez fournir une raison détaillée.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-dark-600">
          <button
            onClick={onClose}
            className="btn-secondary"
            disabled={submitting}
          >
            Fermer
          </button>
          <button
            onClick={handleContest}
            className="btn-danger"
            disabled={submitting}
          >
            Contester
          </button>
          <button
            onClick={handleConfirm}
            className="btn-success flex items-center"
            disabled={submitting}
          >
            {submitting ? (
              <>
                <div className="loading-spinner w-4 h-4 mr-2"></div>
                Validation...
              </>
            ) : (
              <>
                <CheckCircleIcon className="w-4 h-4 mr-2" />
                Valider
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MatchConfirmModal;