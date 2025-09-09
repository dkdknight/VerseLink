import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  UsersIcon,
  PencilIcon,
  TrashIcon,
  UserPlusIcon,
  UserMinusIcon,
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  StarIcon,
  CalendarDaysIcon,
  TrophyIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';
import TeamInvitationModal from '../components/TeamInvitationModal';

const TeamManagementPage = () => {
  const { tournamentId, teamId } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [teamName, setTeamName] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [teamInvitations, setTeamInvitations] = useState([]);
  const [activeTab, setActiveTab] = useState('members');
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (tournamentId && teamId) {
      loadTeamAndTournament();
    }
  }, [tournamentId, teamId]);

  const loadTeamAndTournament = async () => {
    try {
      setLoading(true);
      const [teamData, tournamentData] = await Promise.all([
        tournamentService.getTeamDetails(tournamentId, teamId),
        tournamentService.getTournament(tournamentId)
      ]);
      
      setTeam(teamData);
      setTournament(tournamentData);
      setTeamName(teamData.name);
      
      // Load team invitations if user is captain
      if (teamData.can_manage) {
        await loadTeamInvitations();
      }
      
      // Check if user has permission to manage this team
      if (!teamData.can_manage && !teamData.is_member) {
        toast.error('Vous n\'avez pas accès à cette équipe');
        navigate(`/tournaments/${tournamentId}`);
      }
    } catch (error) {
      console.error('Failed to load team:', error);
      toast.error('Erreur lors du chargement de l\'équipe');
      navigate(`/tournaments/${tournamentId}`);
    } finally {
      setLoading(false);
    }
  };

  const loadTeamInvitations = async () => {
    try {
      const invitations = await tournamentService.getTeamInvitations(tournamentId, teamId);
      setTeamInvitations(invitations);
    } catch (error) {
      console.error('Failed to load team invitations:', error);
    }
  };

  const handleUpdateTeam = async (e) => {
    e.preventDefault();
    
    if (!teamName.trim()) {
      toast.error('Le nom de l\'équipe est requis');
      return;
    }

    try {
      setActionLoading(true);
      await tournamentService.updateTeam(tournamentId, teamId, { name: teamName.trim() });
      toast.success('Équipe mise à jour avec succès !');
      setEditMode(false);
      await loadTeamAndTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la mise à jour de l\'équipe');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTeam = async () => {
    try {
      setActionLoading(true);
      await tournamentService.deleteTeam(tournamentId, teamId);
      toast.success('Équipe supprimée avec succès');
      navigate(`/tournaments/${tournamentId}`);
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la suppression de l\'équipe');
      }
    } finally {
      setActionLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleRemoveMember = async (userId) => {
    try {
      setActionLoading(true);
      await tournamentService.removeTeamMember(tournamentId, teamId, userId);
      toast.success('Membre retiré de l\'équipe');
      await loadTeamAndTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors du retrait du membre');
      }
    } finally {
      setActionLoading(false);
      setMemberToRemove(null);
    }
  };

  const handleLeaveTeam = async () => {
    try {
      setActionLoading(true);
      await tournamentService.leaveTeam(tournamentId, teamId);
      toast.success('Vous avez quitté l\'équipe');
      navigate(`/tournaments/${tournamentId}`);
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la sortie de l\'équipe');
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

  const canEditTeam = () => {
    return team?.can_manage && tournament?.state === 'open_registration';
  };

  const canDeleteTeam = () => {
    return team?.can_manage && tournament?.state === 'open_registration';
  };

  if (loading || !team || !tournament) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Link 
            to={`/tournaments/${tournamentId}`}
            className="flex items-center text-gray-400 hover:text-white mr-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Retour au tournoi
          </Link>
          <div className="flex items-center space-x-3">
            <CogIcon className="w-8 h-8 text-primary-400" />
            <h1 className="text-3xl font-bold text-white">
              Gestion d'équipe
            </h1>
          </div>
        </div>

        {/* Tournament Context */}
        <div className="glass-effect rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">{tournament.name}</h2>
              <p className="text-gray-400 text-sm">
                {formatDate(tournament.start_at_utc)}
              </p>
            </div>
            <div className="text-right">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-white ${
                tournament.state === 'open_registration' ? 'bg-green-600' :
                tournament.state === 'registration_closed' ? 'bg-yellow-600' :
                tournament.state === 'ongoing' ? 'bg-blue-600' :
                'bg-gray-600'
              }`}>
                {tournament.state === 'open_registration' ? 'Inscriptions ouvertes' :
                 tournament.state === 'registration_closed' ? 'Inscriptions fermées' :
                 tournament.state === 'ongoing' ? 'En cours' :
                 tournament.state}
              </span>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Team Information */}
          <div className="lg:col-span-2">
            <div className="glass-effect rounded-xl p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-white flex items-center">
                  <UsersIcon className="w-7 h-7 mr-3 text-primary-400" />
                  {editMode ? 'Modifier l\'équipe' : 'Informations de l\'équipe'}
                </h3>
                
                {team.can_manage && canEditTeam() && !editMode && (
                  <button
                    onClick={() => setEditMode(true)}
                    className="btn-secondary flex items-center"
                  >
                    <PencilIcon className="w-4 h-4 mr-2" />
                    Modifier
                  </button>
                )}
              </div>

              {editMode ? (
                <form onSubmit={handleUpdateTeam} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Nom de l'équipe
                    </label>
                    <input
                      type="text"
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                      className="input-primary w-full"
                      placeholder="Nom de l'équipe"
                      required
                      minLength={2}
                      maxLength={100}
                    />
                  </div>
                  
                  <div className="flex items-center space-x-3 pt-4">
                    <button
                      type="submit"
                      disabled={actionLoading}
                      className="btn-primary flex items-center"
                    >
                      {actionLoading ? 'Sauvegarde...' : 'Sauvegarder'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEditMode(false);
                        setTeamName(team.name);
                      }}
                      className="btn-secondary"
                    >
                      Annuler
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xl font-semibold text-white flex items-center">
                        {team.seed && (
                          <span className="bg-primary-600 text-white text-sm rounded-full w-7 h-7 flex items-center justify-center mr-3 font-bold">
                            {team.seed}
                          </span>
                        )}
                        {team.name}
                      </h4>
                      <p className="text-gray-400">
                        Équipe créée le {formatDate(team.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4 mt-6">
                    <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
                      <div className="flex items-center">
                        <UsersIcon className="w-8 h-8 text-primary-400 mr-3" />
                        <div>
                          <p className="text-2xl font-bold text-white">{team.member_count}</p>
                          <p className="text-sm text-gray-400">
                            Membres ({tournament.team_size} max)
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {tournament.format === 'rr' && (
                      <>
                        <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
                          <div className="flex items-center">
                            <TrophyIcon className="w-8 h-8 text-green-400 mr-3" />
                            <div>
                              <p className="text-2xl font-bold text-white">{team.wins}</p>
                              <p className="text-sm text-gray-400">Victoires</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
                          <div className="flex items-center">
                            <StarIcon className="w-8 h-8 text-yellow-400 mr-3" />
                            <div>
                              <p className="text-2xl font-bold text-white">{team.points}</p>
                              <p className="text-sm text-gray-400">Points</p>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Team Members */}
            <div className="glass-effect rounded-xl p-6">
              <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                <UsersIcon className="w-6 h-6 mr-3 text-primary-400" />
                Membres de l'équipe ({team.members.length})
              </h3>

              <div className="space-y-3">
                {team.members.map((member) => (
                  <div key={member.user_id} className="flex items-center justify-between p-4 bg-dark-700 rounded-lg border border-dark-600">
                    <div className="flex items-center space-x-3">
                      {member.avatar_url ? (
                        <img
                          src={member.avatar_url}
                          alt={member.handle}
                          className="w-10 h-10 rounded-full"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-dark-600 rounded-full flex items-center justify-center">
                          <UsersIcon className="w-5 h-5 text-gray-400" />
                        </div>
                      )}
                      
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium text-white">{member.handle}</h4>
                          {member.is_captain && (
                            <span className="flex items-center text-xs bg-yellow-600 text-white px-2 py-1 rounded-full">
                              <StarIcon className="w-3 h-3 mr-1" />
                              Capitaine
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-400">
                          Rejoint le {formatDate(member.joined_at)}
                        </p>
                      </div>
                    </div>

                    {/* Member Actions */}
                    {team.can_manage && !member.is_captain && canEditTeam() && (
                      <button
                        onClick={() => setMemberToRemove(member)}
                        className="text-red-400 hover:text-red-300 p-2 rounded-lg hover:bg-red-900/20 transition-colors duration-200"
                        title="Retirer de l'équipe"
                      >
                        <UserMinusIcon className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {team.member_count < tournament.team_size && canEditTeam() && (
                <div className="mt-6 p-4 bg-dark-700 rounded-lg border border-dark-600 border-dashed">
                  <div className="text-center">
                    <UserPlusIcon className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                    <p className="text-gray-400 mb-4">
                      Il reste {tournament.team_size - team.member_count} place(s) disponible(s)
                    </p>
                    <button
                      onClick={() => setShowInviteModal(true)}
                      className="btn-primary flex items-center justify-center mx-auto"
                    >
                      <UserPlusIcon className="w-4 h-4 mr-2" />
                      Inviter un joueur
                    </button>
                    <p className="text-sm text-gray-500 mt-3">
                      Les joueurs peuvent également rejoindre votre équipe depuis la page du tournoi
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Actions Panel */}
          <div className="lg:col-span-1">
            <div className="glass-effect rounded-xl p-6 mb-6">
              <h3 className="text-lg font-bold text-white mb-4">Actions</h3>
              
              <div className="space-y-3">
                {/* Leave Team (non-captain) */}
                {team.is_member && !team.can_manage && tournament.state === 'open_registration' && (
                  <button
                    onClick={handleLeaveTeam}
                    disabled={actionLoading}
                    className="w-full btn-danger flex items-center justify-center"
                  >
                    <UserMinusIcon className="w-4 h-4 mr-2" />
                    Quitter l'équipe
                  </button>
                )}

                {/* Delete Team (captain only) */}
                {team.can_manage && canDeleteTeam() && (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    disabled={actionLoading}
                    className="w-full btn-danger flex items-center justify-center"
                  >
                    <TrashIcon className="w-4 h-4 mr-2" />
                    Supprimer l'équipe
                  </button>
                )}
              </div>
              
              {(!canEditTeam() && tournament.state !== 'open_registration') && (
                <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                  <div className="flex items-start">
                    <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mr-2 mt-0.5" />
                    <p className="text-yellow-300 text-sm">
                      Les modifications ne sont plus possibles car les inscriptions sont fermées.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Tournament Info */}
            <div className="glass-effect rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Informations du tournoi</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center text-gray-300">
                  <CalendarDaysIcon className="w-4 h-4 mr-2 text-primary-400" />
                  <span>{formatDate(tournament.start_at_utc)}</span>
                </div>
                
                <div className="flex items-center text-gray-300">
                  <UsersIcon className="w-4 h-4 mr-2 text-primary-400" />
                  <span>
                    {tournament.team_count}/{tournament.max_teams} équipes
                  </span>
                </div>
                
                <div className="flex items-center text-gray-300">
                  <TrophyIcon className="w-4 h-4 mr-2 text-primary-400" />
                  <span>
                    {tournament.format === 'se' ? 'Simple Élimination' :
                     tournament.format === 'de' ? 'Double Élimination' :
                     tournament.format === 'rr' ? 'Round Robin' :
                     'Format personnalisé'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Team Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg max-w-md w-full p-6 border border-red-500/30">
            <div className="flex items-center mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-400 mr-3" />
              <h3 className="text-xl font-bold text-white">Supprimer l'équipe</h3>
            </div>
            
            <p className="text-gray-300 mb-6">
              Êtes-vous sûr de vouloir supprimer l'équipe <strong>{team.name}</strong> ? 
              Cette action est irréversible et retirera tous les membres de l'équipe.
            </p>
            
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary"
                disabled={actionLoading}
              >
                Annuler
              </button>
              <button
                onClick={handleDeleteTeam}
                disabled={actionLoading}
                className="btn-danger flex items-center"
              >
                {actionLoading ? (
                  <>
                    <div className="loading-spinner w-4 h-4 mr-2"></div>
                    Suppression...
                  </>
                ) : (
                  <>
                    <TrashIcon className="w-4 h-4 mr-2" />
                    Supprimer
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Remove Member Confirmation Modal */}
      {memberToRemove && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg max-w-md w-full p-6 border border-red-500/30">
            <div className="flex items-center mb-4">
              <UserMinusIcon className="w-8 h-8 text-red-400 mr-3" />
              <h3 className="text-xl font-bold text-white">Retirer le membre</h3>
            </div>
            
            <p className="text-gray-300 mb-6">
              Êtes-vous sûr de vouloir retirer <strong>{memberToRemove.handle}</strong> de l'équipe ?
            </p>
            
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setMemberToRemove(null)}
                className="btn-secondary"
                disabled={actionLoading}
              >
                Annuler
              </button>
              <button
                onClick={() => handleRemoveMember(memberToRemove.user_id)}
                disabled={actionLoading}
                className="btn-danger flex items-center"
              >
                {actionLoading ? (
                  <>
                    <div className="loading-spinner w-4 h-4 mr-2"></div>
                    Retrait...
                  </>
                ) : (
                  <>
                    <UserMinusIcon className="w-4 h-4 mr-2" />
                    Retirer
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Team Invitation Modal */}
      <TeamInvitationModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        tournamentId={tournamentId}
        teamId={teamId}
        onInvitationSent={loadTeamInvitations}
      />
    </div>
  );
};

export default TeamManagementPage;