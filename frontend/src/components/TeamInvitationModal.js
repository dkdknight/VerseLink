import React, { useState } from 'react';
import { 
  XMarkIcon,
  UserPlusIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { tournamentService } from '../services/tournamentService';

const TeamInvitationModal = ({ isOpen, onClose, tournamentId, teamId, onInvitationSent }) => {
  const [inviteHandle, setInviteHandle] = useState('');
  const [inviteMessage, setInviteMessage] = useState('');
  const [sending, setSending] = useState(false);

  const handleSendInvitation = async (e) => {
    e.preventDefault();
    
    if (!inviteHandle.trim()) {
      toast.error('Le nom d\'utilisateur est requis');
      return;
    }

    try {
      setSending(true);
      await tournamentService.createTeamInvitation(tournamentId, teamId, {
        invited_user_handle: inviteHandle.trim(),
        message: inviteMessage.trim() || null
      });
      
      toast.success('Invitation envoyée avec succès !');
      onInvitationSent();
      onClose();
      
      // Reset form
      setInviteHandle('');
      setInviteMessage('');
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de l\'envoi de l\'invitation');
      }
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    if (!sending) {
      setInviteHandle('');
      setInviteMessage('');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-md w-full p-6 border border-dark-600">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <UserPlusIcon className="w-6 h-6 text-primary-400" />
            <h2 className="text-xl font-semibold text-white">Inviter un joueur</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={sending}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSendInvitation} className="space-y-4">
          {/* Handle Input */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Nom d'utilisateur *
            </label>
            <input
              type="text"
              value={inviteHandle}
              onChange={(e) => setInviteHandle(e.target.value)}
              className="input-primary w-full"
              placeholder="Nom d'utilisateur du joueur"
              required
              minLength={2}
              maxLength={50}
              disabled={sending}
            />
            <p className="text-xs text-gray-400 mt-1">
              Le nom d'utilisateur exact du joueur que vous souhaitez inviter
            </p>
          </div>

          {/* Message Input */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Message personnel (optionnel)
            </label>
            <textarea
              value={inviteMessage}
              onChange={(e) => setInviteMessage(e.target.value)}
              placeholder="Ajoutez un message personnel à votre invitation..."
              rows={3}
              className="input-primary w-full resize-none"
              maxLength={500}
              disabled={sending}
            />
            <p className="text-xs text-gray-400 mt-1">
              {inviteMessage.length}/500 caractères
            </p>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-dark-600">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary"
              disabled={sending}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={sending || !inviteHandle.trim()}
              className="btn-primary flex items-center"
            >
              {sending ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2"></div>
                  Envoi...
                </>
              ) : (
                <>
                  <PaperAirplaneIcon className="w-4 h-4 mr-2" />
                  Envoyer l'invitation
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TeamInvitationModal;