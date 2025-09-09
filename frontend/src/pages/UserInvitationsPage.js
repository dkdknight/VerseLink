import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  InboxIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UsersIcon,
  TrophyIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';

const UserInvitationsPage = () => {
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('pending');
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadInvitations();
    }
  }, [isAuthenticated, statusFilter]);

  const loadInvitations = async () => {
    try {
      setLoading(true);
      const invitationsData = await tournamentService.getMyInvitations(statusFilter || undefined);
      setInvitations(invitationsData);
    } catch (error) {
      console.error('Failed to load invitations:', error);
      toast.error('Erreur lors du chargement des invitations');
    } finally {
      setLoading(false);
    }
  };

  const handleRespondToInvitation = async (invitationId, accept) => {
    try {
      setActionLoading(true);
      await tournamentService.respondToInvitation(invitationId, accept);
      
      const action = accept ? 'acceptée' : 'refusée';
      toast.success(`Invitation ${action} avec succès !`);
      
      await loadInvitations();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la réponse à l\'invitation');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-yellow-400" />;
      case 'accepted':
        return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
      case 'declined':
        return <XCircleIcon className="w-5 h-5 text-red-400" />;
      case 'expired':
        return <XCircleIcon className="w-5 h-5 text-gray-400" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-600 text-white';
      case 'accepted':
        return 'bg-green-600 text-white';
      case 'declined':
        return 'bg-red-600 text-white';
      case 'expired':
        return 'bg-gray-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'En attente';
      case 'accepted':
        return 'Acceptée';
      case 'declined':
        return 'Refusée';
      case 'expired':
        return 'Expirée';
      default:
        return status;
    }
  };

  const isExpired = (invitation) => {
    return new Date(invitation.expires_at) < new Date();
  };

  const InvitationCard = ({ invitation }) => (
    <div className="glass-effect rounded-lg p-6 mb-4">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center mb-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mr-2 ${getStatusColor(invitation.status)}`}>
              {getStatusIcon(invitation.status)}
              <span className="ml-1">{getStatusText(invitation.status)}</span>
            </span>
            {invitation.status === 'pending' && isExpired(invitation) && (
              <span className="text-xs text-red-400 font-medium">
                Expirée
              </span>
            )}
          </div>
          
          <h3 className="text-white font-bold text-lg mb-2">
            Invitation à rejoindre l'équipe "{invitation.team_name}"
          </h3>
          
          <div className="space-y-2 text-sm text-gray-300">
            <div className="flex items-center">
              <TrophyIcon className="w-4 h-4 mr-2 text-primary-400" />
              <span>Tournoi: {invitation.tournament_name}</span>
            </div>
            
            <div className="flex items-center">
              <UsersIcon className="w-4 h-4 mr-2 text-primary-400" />
              <span>Invité par: {invitation.invited_by_handle}</span>
            </div>
            
            <div className="flex items-center">
              <CalendarDaysIcon className="w-4 h-4 mr-2 text-primary-400" />
              <span>Invité le: {formatDate(invitation.created_at)}</span>
            </div>
            
            {invitation.status === 'pending' && (
              <div className="flex items-center">
                <ClockIcon className="w-4 h-4 mr-2 text-yellow-400" />
                <span>Expire le: {formatDate(invitation.expires_at)}</span>
              </div>
            )}
            
            {invitation.responded_at && (
              <div className="flex items-center">
                <CheckCircleIcon className="w-4 h-4 mr-2 text-green-400" />
                <span>Répondu le: {formatDate(invitation.responded_at)}</span>
              </div>
            )}
          </div>
          
          {invitation.message && (
            <div className="mt-4 p-3 bg-dark-700 rounded border border-dark-600">
              <p className="text-sm text-gray-300 italic">
                "{invitation.message}"
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-dark-600">
        <Link
          to={`/tournaments/${invitation.tournament_id}`}
          className="text-primary-400 hover:text-primary-300 text-sm font-medium"
        >
          Voir le tournoi →
        </Link>
        
        {invitation.status === 'pending' && !isExpired(invitation) && (
          <div className="flex space-x-3">
            <button
              onClick={() => handleRespondToInvitation(invitation.id, false)}
              disabled={actionLoading}
              className="btn-secondary text-sm flex items-center"
            >
              <XCircleIcon className="w-4 h-4 mr-1" />
              Refuser
            </button>
            <button
              onClick={() => handleRespondToInvitation(invitation.id, true)}
              disabled={actionLoading}
              className="btn-primary text-sm flex items-center"
            >
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              Accepter
            </button>
          </div>
        )}
      </div>
    </div>
  );

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Connexion requise</h1>
          <p className="text-gray-400 mb-8">
            Vous devez être connecté pour voir vos invitations.
          </p>
          <Link to="/login" className="btn-primary">
            Se connecter
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <InboxIcon className="w-8 h-8 text-primary-400" />
            <h1 className="text-3xl font-bold text-white text-shadow">
              Mes invitations d'équipe
            </h1>
          </div>
          <p className="text-xl text-gray-400">
            Gérez vos invitations à rejoindre des équipes de tournoi
          </p>
        </div>

        {/* Status Filter */}
        <div className="glass-effect rounded-lg p-4 mb-8">
          <div className="flex flex-wrap gap-3 justify-center">
            {[
              { value: 'pending', label: 'En attente', icon: ClockIcon },
              { value: 'accepted', label: 'Acceptées', icon: CheckCircleIcon },
              { value: 'declined', label: 'Refusées', icon: XCircleIcon },
              { value: '', label: 'Toutes', icon: InboxIcon }
            ].map((status) => (
              <button
                key={status.value}
                onClick={() => setStatusFilter(status.value)}
                className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                  statusFilter === status.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-gray-300 hover:bg-dark-600 hover:text-white'
                }`}
              >
                <status.icon className="w-4 h-4 mr-2" />
                {status.label}
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="text-center py-16">
            <div className="loading-spinner w-12 h-12 mx-auto"></div>
          </div>
        ) : invitations.length > 0 ? (
          <>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white">
                {invitations.length} invitation{invitations.length > 1 ? 's' : ''} trouvée{invitations.length > 1 ? 's' : ''}
              </h2>
            </div>
            
            <div className="space-y-4">
              {invitations.map((invitation) => (
                <InvitationCard key={invitation.id} invitation={invitation} />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <InboxIcon className="w-24 h-24 text-gray-600 mx-auto mb-6" />
            <h3 className="text-2xl font-bold text-white mb-4">Aucune invitation trouvée</h3>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              {statusFilter === 'pending' 
                ? "Vous n'avez aucune invitation en attente."
                : statusFilter 
                ? `Vous n'avez aucune invitation ${getStatusText(statusFilter).toLowerCase()}.`
                : "Vous n'avez reçu aucune invitation d'équipe."
              }
            </p>
            <Link to="/tournaments" className="btn-primary">
              Parcourir les tournois
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserInvitationsPage;