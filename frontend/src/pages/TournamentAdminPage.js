import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  CogIcon,
  PlayIcon,
  StopIcon,
  LockClosedIcon,
  LockOpenIcon,
  TrophyIcon,
  UsersIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';

const TournamentAdminPage = () => {
  const { id } = useParams();
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(null);
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (id) {
      loadTournament();
    }
  }, [id]);

  const loadTournament = async () => {
    try {
      setLoading(true);
      const tournamentData = await tournamentService.getTournament(id);
      setTournament(tournamentData);
      
      // Check if user has admin permissions
      if (!tournamentData.can_edit) {
        toast.error('Vous n\'avez pas les permissions d\'administration pour ce tournoi');
        return;
      }
    } catch (error) {
      console.error('Failed to load tournament:', error);
      toast.error('Tournoi non trouvé');
    } finally {
      setLoading(false);
    }
  };

  const handleStartTournament = async () => {
    try {
      setActionLoading(true);
      await tournamentService.startTournament(tournament.id);
      toast.success('Tournoi démarré avec succès !');
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors du démarrage du tournoi');
      }
    } finally {
      setActionLoading(false);
      setShowConfirmModal(null);
    }
  };

  const handleCloseRegistration = async () => {
    try {
      setActionLoading(true);
      await tournamentService.closeTournamentRegistration(tournament.id);
      toast.success('Inscriptions fermées avec succès !');
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la fermeture des inscriptions');
      }
    } finally {
      setActionLoading(false);
      setShowConfirmModal(null);
    }
  };

  const handleReopenRegistration = async () => {
    try {
      setActionLoading(true);
      await tournamentService.reopenTournamentRegistration(tournament.id);
      toast.success('Inscriptions rouvertes avec succès !');
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la réouverture des inscriptions');
      }
    } finally {
      setActionLoading(false);
      setShowConfirmModal(null);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStateColor = (state) => {
    const colors = {
      draft: 'bg-gray-600',
      open_registration: 'bg-green-600',
      registration_closed: 'bg-yellow-600',
      ongoing: 'bg-blue-600',
      finished: 'bg-purple-600',
      cancelled: 'bg-red-600'
    };
    return colors[state] || 'bg-gray-600';
  };

  const formatTournamentState = (state) => {
    const states = {
      draft: 'Brouillon',
      open_registration: 'Inscriptions ouvertes',
      registration_closed: 'Inscriptions fermées',
      ongoing: 'En cours',
      finished: 'Terminé',
      cancelled: 'Annulé'
    };
    return states[state] || state;
  };

  const getAvailableActions = () => {
    const actions = [];

    switch (tournament?.state) {
      case 'open_registration':
        actions.push({
          key: 'close_registration',
          label: 'Fermer les inscriptions',
          description: 'Empêcher de nouvelles équipes de s\'inscrire',
          icon: LockClosedIcon,
          variant: 'primary',
          action: () => setShowConfirmModal('close_registration')
        });
        break;

      case 'registration_closed':
        actions.push({
          key: 'start_tournament',
          label: 'Démarrer le tournoi',
          description: 'Générer le bracket et commencer la compétition',
          icon: PlayIcon,
          variant: 'success',
          action: () => setShowConfirmModal('start_tournament'),
          condition: tournament.team_count >= 2
        });
        
        actions.push({
          key: 'reopen_registration',
          label: 'Rouvrir les inscriptions',
          description: 'Permettre à d\'autres équipes de s\'inscrire',
          icon: LockOpenIcon,
          variant: 'secondary',
          action: () => setShowConfirmModal('reopen_registration')
        });
        break;

      case 'ongoing':
        // Tournament management actions could go here
        break;

      case 'finished':
        // Post-tournament actions could go here
        break;
    }

    return actions;
  };

  const ConfirmModal = ({ type, onConfirm, onCancel }) => {
    const modals = {
      start_tournament: {
        title: 'Démarrer le tournoi',
        message: 'Êtes-vous sûr de vouloir démarrer le tournoi ? Le bracket sera généré et les inscriptions seront définitivement fermées.',
        confirmText: 'Démarrer',
        confirmClass: 'btn-success',
        icon: PlayIcon,
        iconColor: 'text-green-400'
      },
      close_registration: {
        title: 'Fermer les inscriptions',
        message: 'Voulez-vous fermer les inscriptions ? Aucune nouvelle équipe ne pourra s\'inscrire.',
        confirmText: 'Fermer',
        confirmClass: 'btn-primary',
        icon: LockClosedIcon,
        iconColor: 'text-primary-400'
      },
      reopen_registration: {
        title: 'Rouvrir les inscriptions',
        message: 'Voulez-vous rouvrir les inscriptions ? D\'autres équipes pourront s\'inscrire.',
        confirmText: 'Rouvrir',
        confirmClass: 'btn-secondary',
        icon: LockOpenIcon,
        iconColor: 'text-gray-400'
      }
    };

    const modal = modals[type];
    if (!modal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
        <div className="bg-dark-800 rounded-lg max-w-md w-full p-6 border border-dark-600">
          <div className="flex items-center mb-4">
            <modal.icon className={`w-8 h-8 ${modal.iconColor} mr-3`} />
            <h3 className="text-xl font-bold text-white">{modal.title}</h3>
          </div>
          
          <p className="text-gray-300 mb-6">{modal.message}</p>
          
          <div className="flex items-center justify-end space-x-3">
            <button
              onClick={onCancel}
              className="btn-secondary"
              disabled={actionLoading}
            >
              Annuler
            </button>
            <button
              onClick={onConfirm}
              disabled={actionLoading}
              className={`${modal.confirmClass} flex items-center`}
            >
              {actionLoading ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2"></div>
                  Chargement...
                </>
              ) : (
                <>
                  <modal.icon className="w-4 h-4 mr-2" />
                  {modal.confirmText}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading || !tournament) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  if (!tournament.can_edit) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Accès refusé</h1>
          <p className="text-gray-400 mb-8">
            Vous n'avez pas les permissions d'administration pour ce tournoi.
          </p>
          <Link to={`/tournaments/${id}`} className="btn-primary">
            Retour au tournoi
          </Link>
        </div>
      </div>
    );
  }

  const availableActions = getAvailableActions();

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Link 
            to={`/tournaments/${id}`}
            className="flex items-center text-gray-400 hover:text-white mr-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Retour au tournoi
          </Link>
          <div className="flex items-center space-x-3">
            <CogIcon className="w-8 h-8 text-primary-400" />
            <h1 className="text-3xl font-bold text-white">
              Administration du tournoi
            </h1>
          </div>
        </div>

        {/* Tournament Overview */}
        <div className="glass-effect rounded-xl p-8 mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div className="flex-1">
              <div className="flex items-center mb-4">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mr-3 text-white ${getStateColor(tournament.state)}`}>
                  {formatTournamentState(tournament.state)}
                </span>
                <Link 
                  to={`/organizations/${tournament.org_id}`}
                  className="text-primary-400 hover:text-primary-300 font-medium"
                >
                  {tournament.org_name} ({tournament.org_tag})
                </Link>
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-4">{tournament.name}</h2>
              
              <div className="grid md:grid-cols-2 gap-4 text-gray-300">
                <div className="flex items-center">
                  <CalendarDaysIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>{formatDate(tournament.start_at_utc)}</span>
                </div>
                
                <div className="flex items-center">
                  <TrophyIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>
                    {tournament.format === 'se' ? 'Simple Élimination' :
                     tournament.format === 'de' ? 'Double Élimination' :
                     tournament.format === 'rr' ? 'Round Robin' :
                     'Format personnalisé'}
                  </span>
                </div>
                
                <div className="flex items-center">
                  <UsersIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>
                    {tournament.team_count}/{tournament.max_teams} équipes
                    <span className="mx-2">•</span>
                    {tournament.team_size} joueurs/équipe
                  </span>
                </div>
                
                {tournament.current_round > 0 && (
                  <div className="flex items-center">
                    <ChartBarIcon className="w-5 h-5 mr-2 text-primary-400" />
                    <span>
                      Round {tournament.current_round}/{tournament.rounds_total}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Statistics */}
          <div className="lg:col-span-2">
            <div className="glass-effect rounded-xl p-6 mb-6">
              <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                <ChartBarIcon className="w-6 h-6 mr-3 text-primary-400" />
                Statistiques du tournoi
              </h3>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-dark-700 rounded-lg p-4 border border-dark-600 text-center">
                  <div className="text-2xl font-bold text-white mb-1">{tournament.team_count}</div>
                  <div className="text-sm text-gray-400">Équipes inscrites</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {tournament.max_teams - tournament.team_count} places restantes
                  </div>
                </div>
                
                <div className="bg-dark-700 rounded-lg p-4 border border-dark-600 text-center">
                  <div className="text-2xl font-bold text-white mb-1">
                    {tournament.team_count * tournament.team_size}
                  </div>
                  <div className="text-sm text-gray-400">Joueurs inscrits</div>
                </div>
                
                <div className="bg-dark-700 rounded-lg p-4 border border-dark-600 text-center">
                  <div className="text-2xl font-bold text-white mb-1">{tournament.matches?.length || 0}</div>
                  <div className="text-sm text-gray-400">Matches total</div>
                </div>
                
                <div className="bg-dark-700 rounded-lg p-4 border border-dark-600 text-center">
                  <div className="text-2xl font-bold text-white mb-1">
                    {tournament.matches?.filter(m => m.state === 'verified').length || 0}
                  </div>
                  <div className="text-sm text-gray-400">Matches terminés</div>
                </div>
              </div>
            </div>

            {/* Team List */}
            <div className="glass-effect rounded-xl p-6">
              <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                <UsersIcon className="w-6 h-6 mr-3 text-primary-400" />
                Équipes inscrites ({tournament.teams?.length || 0})
              </h3>
              
              {tournament.teams && tournament.teams.length > 0 ? (
                <div className="space-y-3">
                  {tournament.teams.map((team) => (
                    <div key={team.id} className="flex items-center justify-between p-4 bg-dark-700 rounded-lg border border-dark-600">
                      <div className="flex items-center space-x-3">
                        {team.seed && (
                          <span className="bg-primary-600 text-white text-sm rounded-full w-7 h-7 flex items-center justify-center font-bold">
                            {team.seed}
                          </span>
                        )}
                        <div>
                          <h4 className="font-medium text-white">{team.name}</h4>
                          <p className="text-sm text-gray-400">
                            Capitaine: {team.captain_handle} • {team.member_count} membres
                          </p>
                        </div>
                      </div>
                      
                      {tournament.format === 'rr' && (
                        <div className="text-right text-sm">
                          <div className="text-white font-medium">
                            {team.wins}V - {team.losses}D
                          </div>
                          <div className="text-gray-400">{team.points} pts</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <UsersIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">Aucune équipe inscrite</p>
                </div>
              )}
            </div>
          </div>

          {/* Actions Panel */}
          <div className="lg:col-span-1">
            <div className="glass-effect rounded-xl p-6 mb-6">
              <h3 className="text-lg font-bold text-white mb-6">Actions disponibles</h3>
              
              {availableActions.length > 0 ? (
                <div className="space-y-3">
                  {availableActions.map((action) => (
                    <div key={action.key}>
                      {action.condition !== false && (
                        <button
                          onClick={action.action}
                          disabled={actionLoading}
                          className={`w-full ${action.variant === 'success' ? 'btn-success' : 
                                              action.variant === 'primary' ? 'btn-primary' : 
                                              action.variant === 'danger' ? 'btn-danger' : 'btn-secondary'} 
                                      flex items-center justify-center p-4 rounded-lg`}
                        >
                          <action.icon className="w-5 h-5 mr-3" />
                          <div className="text-left">
                            <div className="font-medium">{action.label}</div>
                            <div className="text-xs opacity-80">{action.description}</div>
                          </div>
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <CheckCircleIcon className="w-12 h-12 text-green-400 mx-auto mb-3" />
                  <p className="text-gray-400 text-sm">
                    Aucune action requise pour le moment
                  </p>
                </div>
              )}
              
              {/* Warnings */}
              {tournament.state === 'registration_closed' && tournament.team_count < 2 && (
                <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                  <div className="flex items-start">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mr-2 mt-0.5" />
                    <p className="text-red-300 text-sm">
                      Le tournoi nécessite au moins 2 équipes pour être démarré.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="glass-effect rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Résumé</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">État:</span>
                  <span className="text-white font-medium">
                    {formatTournamentState(tournament.state)}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">Progression:</span>
                  <span className="text-white font-medium">
                    {tournament.current_round > 0 ? 
                      `${Math.round((tournament.current_round / tournament.rounds_total) * 100)}%` : 
                      '0%'
                    }
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">Créé le:</span>
                  <span className="text-white">
                    {new Date(tournament.created_at).toLocaleDateString('fr-FR')}
                  </span>
                </div>
                
                {tournament.winner_team_name && (
                  <div className="flex justify-between pt-2 border-t border-dark-600">
                    <span className="text-gray-400">Gagnant:</span>
                    <span className="text-accent-gold font-medium flex items-center">
                      <TrophyIcon className="w-4 h-4 mr-1" />
                      {tournament.winner_team_name}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modals */}
      {showConfirmModal && (
        <ConfirmModal
          type={showConfirmModal}
          onConfirm={() => {
            switch (showConfirmModal) {
              case 'start_tournament':
                handleStartTournament();
                break;
              case 'close_registration':
                handleCloseRegistration();
                break;
              case 'reopen_registration':
                handleReopenRegistration();
                break;
            }
          }}
          onCancel={() => setShowConfirmModal(null)}
        />
      )}
    </div>
  );
};

export default TournamentAdminPage;