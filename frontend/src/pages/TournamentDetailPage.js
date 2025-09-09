import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  TrophyIcon,
  CalendarDaysIcon,
  UsersIcon,
  TagIcon,
  PlusIcon,
  DocumentArrowUpIcon,
  CheckCircleIcon,
  ClockIcon,
  PlayIcon,
  StarIcon,
  CogIcon,
  LockClosedIcon,
  LockOpenIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';
import MatchReportModal from '../components/MatchReportModal';
import TournamentBracket from '../components/TournamentBracket';
import MatchDisputeModal from '../components/MatchDisputeModal';

const TournamentDetailPage = () => {
  const { id } = useParams();
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('bracket');
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [disputeModalOpen, setDisputeModalOpen] = useState(false);
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
    } catch (error) {
      console.error('Failed to load tournament:', error);
      toast.error('Tournoi non trouvé');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeam = async (teamName) => {
    if (!isAuthenticated) {
      toast.error('Vous devez être connecté pour créer une équipe');
      return;
    }

    try {
      setActionLoading(true);
      await tournamentService.createTeam(tournament.id, { name: teamName });
      toast.success('Équipe créée avec succès !');
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("Erreur lors de la création de l'équipe");
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleJoinTeam = async (teamId) => {
    if (!isAuthenticated || !user) {
      toast.error('Vous devez être connecté pour rejoindre une équipe');
      return;
    }

    try {
      setActionLoading(true);
      await tournamentService.addTeamMember(tournament.id, teamId, user.id);
      toast.success("Vous avez rejoint l'équipe !");
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("Erreur lors de l'adhésion à l'équipe");
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleMatchClick = (match) => {
    setSelectedMatch(match);
    if (match.state === 'pending' && canReportScore(match)) {
      setReportModalOpen(true);
    } else if (canDispute(match)) {
      setDisputeModalOpen(true);
    }
  };

  const canReportScore = (match) => {
    if (!isAuthenticated || !user) return false;
    // Check if user is capitaine d'une des équipes
    return (
      match.can_report ||
      match.team_a_captain_id === user.id ||
      match.team_b_captain_id === user.id
    );
  };

  const canDispute = (match) => {
    if (!isAuthenticated || !user) return false;
    return (
      ['reported', 'verified'].includes(match.state) &&
      (match.team_a_captain_id === user.id || match.team_b_captain_id === user.id)
    );
  };

  const canScheduleMatch = (match) => {
    if (!isAuthenticated || !user) return false;

    return (
      match.state === 'pending' &&
      !match.scheduled_at &&
      (match.team_a_captain_id === user.id || match.team_b_captain_id === user.id)
    );
  };

  const canVerifyMatch = (match) => {
    if (!isAuthenticated || !user) return false;
    return match.state === 'reported' && match.can_verify;
  };

  const canUploadAttachment = (match) => {
    if (!isAuthenticated || !user) return false;
    return canReportScore(match) || match.can_verify;
  };

  const handleScheduleMatch = async (match) => {
    const input = prompt('Date et heure du match (YYYY-MM-DD HH:MM)');
    if (!input) return;

    const scheduledAt = new Date(input);
    if (isNaN(scheduledAt)) {
      toast.error('Date invalide');
      return;
    }

    try {
      setActionLoading(true);
      await tournamentService.scheduleMatch(match.id, scheduledAt.toISOString());
      toast.success('Match programmé');
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la programmation du match');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerifyMatch = async (match) => {
    try {
      setActionLoading(true);
      await tournamentService.verifyMatchResult(match.id);
      toast.success('Match vérifié');
      await loadTournament();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la vérification du match');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const formatTournamentFormat = (format) => {
    const formats = {
      se: 'Simple Élimination',
      de: 'Double Élimination',
      rr: 'Round Robin',
      swiss: 'Système Suisse',
    };
    return formats[format] || format;
  };

  const formatTournamentState = (state) => {
    const states = {
      draft: 'Brouillon',
      open_registration: 'Inscriptions ouvertes',
      registration_closed: 'Inscriptions fermées',
      ongoing: 'En cours',
      finished: 'Terminé',
      cancelled: 'Annulé',
    };
    return states[state] || state;
  };

  const getStateColor = (state) => {
    const colors = {
      draft: 'bg-gray-600',
      open_registration: 'bg-green-600',
      registration_closed: 'bg-yellow-600',
      ongoing: 'bg-blue-600',
      finished: 'bg-purple-600',
      cancelled: 'bg-red-600',
    };
    return colors[state] || 'bg-gray-600';
  };

  const TeamCard = ({ team }) => (
    <div className="glass-effect rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-white font-semibold text-lg flex items-center">
            {team.seed && (
              <span className="bg-primary-600 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center mr-2">
                {team.seed}
              </span>
            )}
            {team.name}
          </h4>
          <p className="text-gray-400 text-sm">Capitaine: {team.captain_handle}</p>
        </div>

        <div className="text-right">
          <div className="text-sm text-gray-300">
            {team.member_count}/{tournament.team_size} membres
          </div>
          {tournament.format === 'rr' && (
            <div className="text-xs text-gray-400">
              {team.wins}V - {team.losses}D ({team.points} pts)
            </div>
          )}
        </div>
      </div>

      {/* Team Members */}
      <div className="space-y-1">
        {team.members.slice(0, 3).map((member) => (
          <div key={member.user_id} className="flex items-center text-sm text-gray-300">
            {member.avatar_url ? (
              <img src={member.avatar_url} alt={member.handle} className="w-4 h-4 rounded-full mr-2" />
            ) : (
              <div className="w-4 h-4 bg-dark-600 rounded-full mr-2"></div>
            )}
            <span>{member.handle}</span>
            {member.is_captain && <StarIcon className="w-3 h-3 text-yellow-400 ml-1" />}
          </div>
        ))}
        {team.members.length > 3 && (
          <div className="text-xs text-gray-500">+{team.members.length - 3} autres membres</div>
        )}
      </div>

      {tournament.can_register &&
        isAuthenticated &&
        !tournament.my_team &&
        team.member_count < tournament.team_size && (
          <div className="mt-3 text-center">
            <button
              onClick={() => handleJoinTeam(team.id)}
              disabled={actionLoading}
              className="text-sm text-primary-400 hover:text-primary-300 font-medium"
            >
              Rejoindre l'équipe →
            </button>
          </div>
        )}

      {/* Team Management Link for Captain */}
      {tournament.my_team && tournament.my_team.id === team.id && tournament.my_team.can_manage && (
        <div className="mt-3 text-center">
          <Link
            to={`/tournaments/${tournament.id}/teams/${team.id}/manage`}
            className="text-sm text-primary-400 hover:text-primary-300 font-medium"
          >
            Gérer l'équipe →
          </Link>
        </div>
      )}
    </div>
  );

  const MatchCard = ({ match }) => {
    const fileInputRef = useRef(null);

    const handleFileChange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const description = prompt('Description de la preuve (optionnel)') || '';
      try {
        await tournamentService.uploadMatchAttachment(match.id, file, description);
        toast.success('Preuve envoyée');
        await loadTournament();
      } catch (error) {
        if (error.response?.data?.detail) {
          toast.error(error.response.data.detail);
        } else {
          toast.error("Erreur lors de l'envoi de la preuve");
        }
      } finally {
        e.target.value = '';
      }
    };

    return (
      <div className="glass-effect rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="text-xs bg-dark-600 text-gray-300 px-2 py-1 rounded">Round {match.round}</span>
            <span
              className={`ml-2 text-xs px-2 py-1 rounded text-white ${
                match.state === 'verified'
                  ? 'bg-green-600'
                  : match.state === 'reported'
                  ? 'bg-yellow-600'
                  : match.state === 'live'
                  ? 'bg-blue-600'
                  : 'bg-gray-600'
              }`}
            >
              {match.state === 'verified'
                ? 'Terminé'
                : match.state === 'reported'
                ? 'Reporté'
                : match.state === 'live'
                ? 'En cours'
                : 'À venir'}
            </span>
          </div>

          {match.scheduled_at && (
            <div className="text-xs text-gray-400">
              {new Date(match.scheduled_at).toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="text-white">
            <div className={`font-medium ${match.winner_team_id === match.team_a_id ? 'text-green-400' : ''}`}>
              {match.team_a_name || 'TBD'}
            </div>
            <div className={`font-medium ${match.winner_team_id === match.team_b_id ? 'text-green-400' : ''}`}>
              {match.team_b_name || 'TBD'}
            </div>
          </div>

          {match.score_a !== null && match.score_b !== null && (
            <div className="text-right">
              <div
                className={`font-bold ${
                  match.winner_team_id === match.team_a_id ? 'text-green-400' : 'text-gray-400'
                }`}
              >
                {match.score_a}
              </div>
              <div
                className={`font-bold ${
                  match.winner_team_id === match.team_b_id ? 'text-green-400' : 'text-gray-400'
                }`}
              >
                {match.score_b}
              </div>
            </div>
          )}
        </div>

        {match.notes && <div className="mt-2 text-xs text-gray-400 italic">{match.notes}</div>}

        {match.attachments && match.attachments.length > 0 && (
          <div className="mt-2 text-xs space-y-1">
            {match.attachments.map((att) => (
              <a
                key={att.id}
                href={tournamentService.downloadAttachment(att.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-primary-400 hover:text-primary-300"
              >
                {att.description || att.filename}
              </a>
            ))}
          </div>
        )}

        {/* Actions */}
        {(canScheduleMatch(match) ||
          (canReportScore(match) && match.state === 'pending') ||
          canVerifyMatch(match) ||
          canUploadAttachment(match)) && (
          <div className="mt-3 text-center space-y-2">
            {canScheduleMatch(match) && (
              <button
                onClick={() => handleScheduleMatch(match)}
                disabled={actionLoading}
                className="text-sm text-primary-400 hover:text-primary-300 font-medium block w-full"
              >
                Programmer le match →
              </button>
            )}
            {canReportScore(match) && match.state === 'pending' && (
              <button
                onClick={() => handleMatchClick(match)}
                className="text-sm text-primary-400 hover:text-primary-300 font-medium block w-full"
              >
                Reporter le score →
              </button>
            )}
            {canVerifyMatch(match) && (
              <button
                onClick={() => handleVerifyMatch(match)}
                disabled={actionLoading}
                className="text-sm text-primary-400 hover:text-primary-300 font-medium block w-full"
              >
                Vérifier le match →
              </button>
            )}
            {canUploadAttachment(match) && (
              <>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
                <button
                  onClick={() => fileInputRef.current && fileInputRef.current.click()}
                  className="text-sm text-primary-400 hover:text-primary-300 font-medium block w-full flex items-center justify-center"
                >
                  <DocumentArrowUpIcon className="w-4 h-4 mr-1" /> Envoyer une preuve →
                </button>
              </>
            )}
          </div>
        )}
      </div>
    );
  };

  const BracketView = () => {
    return <TournamentBracket tournament={tournament} onMatchClick={handleMatchClick} />;
  };

  const CreateTeamForm = () => {
    const [teamName, setTeamName] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      if (teamName.trim()) {
        handleCreateTeam(teamName.trim());
        setTeamName('');
      }
    };

    return (
      <form onSubmit={handleSubmit} className="glass-effect rounded-lg p-6">
        <h3 className="text-xl font-bold text-white mb-4">Créer une équipe</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Nom de l'équipe</label>
            <input
              type="text"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              className="input-primary w-full"
              placeholder="Entrez le nom de votre équipe"
              required
              minLength={2}
              maxLength={100}
            />
          </div>
          <button
            type="submit"
            disabled={actionLoading || !teamName.trim()}
            className="btn-primary w-full flex items-center justify-center"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            {actionLoading ? 'Création...' : "Créer l'équipe"}
          </button>
        </div>
      </form>
    );
  };

  if (loading || !tournament) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  // ✅ Affichage conditionnel du bloc Admin (corrige l’ancienne parenthèse orpheline)
  const isTournamentAdmin = tournament?.can_admin || tournament?.can_manage || tournament?.is_admin || false;

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="glass-effect rounded-2xl p-8 mb-8">
          <div className="flex flex-col lg:flex-row">
            {/* Tournament Info */}
            <div className="flex-1">
              <div className="flex items-center mb-4">
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mr-3 text-white ${getStateColor(
                    tournament.state
                  )}`}
                >
                  {formatTournamentState(tournament.state)}
                </span>
                <Link
                  to={`/organizations/${tournament.org_id}`}
                  className="text-primary-400 hover:text-primary-300 font-medium"
                >
                  {tournament.org_name} ({tournament.org_tag})
                </Link>
              </div>

              <h1 className="text-4xl font-bold text-white mb-4 text-shadow">{tournament.name}</h1>

              <div className="grid md:grid-cols-2 gap-4 mb-6 text-gray-300">
                <div className="flex items-center">
                  <CalendarDaysIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>
                    {new Date(tournament.start_at_utc).toLocaleDateString('fr-FR', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>

                <div className="flex items-center">
                  <TrophyIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>{formatTournamentFormat(tournament.format)}</span>
                </div>

                <div className="flex items-center">
                  <UsersIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>
                    {tournament.team_count}/{tournament.max_teams} équipes
                    <span className="mx-2">•</span>
                    {tournament.team_size} joueurs/équipe
                  </span>
                </div>

                {tournament.prize_pool && (
                  <div className="flex items-center">
                    <StarIcon className="w-5 h-5 mr-2 text-accent-gold" />
                    <span className="text-accent-gold font-medium">{tournament.prize_pool}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Banner */}
            {tournament.banner_url && (
              <div className="lg:ml-8 mt-6 lg:mt-0">
                <img
                  src={tournament.banner_url}
                  alt={tournament.name}
                  className="w-full lg:w-64 h-40 object-cover rounded-xl"
                />
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <nav className="flex space-x-8">
            {['bracket', 'teams', 'matches'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-primary-500 text-primary-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                {tab === 'bracket'
                  ? 'Bracket'
                  : tab === 'teams'
                  ? `Équipes (${tournament.teams.length})`
                  : tab === 'matches'
                  ? `Matches (${tournament.matches.length})`
                  : tab}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'bracket' && (
            <div className="card p-6">
              <BracketView />
            </div>
          )}

          {activeTab === 'teams' && (
            <div className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <div className="card p-6">
                  <h3 className="text-2xl font-bold text-white mb-6">Équipes ({tournament.teams.length})</h3>

                  {tournament.teams.length > 0 ? (
                    <div className="grid gap-4">
                      {tournament.teams.map((team) => (
                        <TeamCard key={team.id} team={team} />
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

              {/* Registration */}
              <div className="lg:col-span-1">
                {tournament.can_register && isAuthenticated && !tournament.my_team && <CreateTeamForm />}

                {tournament.my_team && (
                  <div className="glass-effect rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">Mon équipe</h3>
                      {tournament.my_team.can_manage && (
                        <Link
                          to={`/tournaments/${tournament.id}/teams/${tournament.my_team.id}/manage`}
                          className="btn-secondary flex items-center text-sm"
                        >
                          <CogIcon className="w-4 h-4 mr-1" />
                          Gérer
                        </Link>
                      )}
                    </div>
                    <TeamCard team={tournament.my_team} />
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'matches' && (
            <div className="card p-6">
              <h3 className="text-2xl font-bold text-white mb-6">Matches ({tournament.matches.length})</h3>

              {tournament.matches.length > 0 ? (
                <div className="space-y-4">
                  {tournament.matches.map((match) => (
                    <MatchCard key={match.id} match={match} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <PlayIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">Aucun match programmé</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="glass-effect rounded-lg p-4 mb-6">
          <div className="flex flex-wrap gap-4 justify-center">
            {tournament.can_register && isAuthenticated && !tournament.my_team && (
              <Link to={`/tournaments/${tournament.id}/players`} className="btn-secondary flex items-center">
                <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
                Recherche d'équipiers
              </Link>
            )}
          </div>
        </div>

        {/* Admin Actions - Only show to tournament admins */}
        {isTournamentAdmin && (
          <div className="glass-effect rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <CogIcon className="w-5 h-5 text-primary-400" />
                <span className="font-medium text-white">Administration</span>
              </div>

              <div className="flex space-x-3">
                <Link to={`/tournaments/${tournament.id}/admin`} className="btn-secondary flex items-center">
                  <CogIcon className="w-4 h-4 mr-2" />
                  Gérer le tournoi
                </Link>

                {tournament.state === 'open_registration' && tournament.team_count >= 2 && (
                  <button
                    onClick={async () => {
                      try {
                        await tournamentService.closeTournamentRegistration(tournament.id);
                        toast.success('Inscriptions fermées');
                        await loadTournament();
                      } catch (error) {
                        toast.error('Erreur lors de la fermeture des inscriptions');
                      }
                    }}
                    className="btn-primary flex items-center"
                  >
                    <LockClosedIcon className="w-4 h-4 mr-2" />
                    Fermer inscriptions
                  </button>
                )}

                {tournament.state === 'registration_closed' && tournament.team_count >= 2 && (
                  <button
                    onClick={async () => {
                      try {
                        await tournamentService.startTournament(tournament.id);
                        toast.success('Tournoi démarré !');
                        await loadTournament();
                      } catch (error) {
                        toast.error('Erreur lors du démarrage du tournoi');
                      }
                    }}
                    className="btn-success flex items-center"
                  >
                    <PlayIcon className="w-4 h-4 mr-2" />
                    Démarrer
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Description */}
        <div className="card p-6 mt-6">
          <h3 className="text-2xl font-bold text-white mb-4">Description</h3>
          <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">{tournament.description}</div>
        </div>
      </div>

      {/* Match Report Modal */}
      <MatchReportModal
        isOpen={reportModalOpen}
        onClose={() => {
          setReportModalOpen(false);
          setSelectedMatch(null);
        }}
        match={selectedMatch}
        currentUser={user}
        onMatchUpdated={loadTournament}
      />

      {/* Match Dispute Modal */}
      <MatchDisputeModal
        isOpen={disputeModalOpen}
        onClose={() => {
          setDisputeModalOpen(false);
          setSelectedMatch(null);
        }}
        match={selectedMatch}
        onDisputeCreated={loadTournament}
      />
    </div>
  );
};

export default TournamentDetailPage;
