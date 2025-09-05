import React, { useState, useEffect } from 'react';
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
  StarIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';
import MatchReportModal from '../components/MatchReportModal';
import TournamentBracket from '../components/TournamentBracket';

const TournamentDetailPage = () => {
  const { id } = useParams();
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('bracket');
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
        toast.error('Erreur lors de la création de l\'équipe');
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
      swiss: 'Système Suisse'
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
      cancelled: 'Annulé'
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
      cancelled: 'bg-red-600'
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
          <p className="text-gray-400 text-sm">
            Capitaine: {team.captain_handle}
          </p>
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
              <img
                src={member.avatar_url}
                alt={member.handle}
                className="w-4 h-4 rounded-full mr-2"
              />
            ) : (
              <div className="w-4 h-4 bg-dark-600 rounded-full mr-2"></div>
            )}
            <span>{member.handle}</span>
            {member.is_captain && (
              <StarIcon className="w-3 h-3 text-yellow-400 ml-1" />
            )}
          </div>
        ))}
        {team.members.length > 3 && (
          <div className="text-xs text-gray-500">
            +{team.members.length - 3} autres membres
          </div>
        )}
      </div>
    </div>
  );

  const MatchCard = ({ match }) => (
    <div className="glass-effect rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs bg-dark-600 text-gray-300 px-2 py-1 rounded">
            Round {match.round}
          </span>
          <span className={`ml-2 text-xs px-2 py-1 rounded text-white ${
            match.state === 'verified' ? 'bg-green-600' :
            match.state === 'reported' ? 'bg-yellow-600' :
            match.state === 'live' ? 'bg-blue-600' :
            'bg-gray-600'
          }`}>
            {match.state === 'verified' ? 'Terminé' :
             match.state === 'reported' ? 'Reporté' :
             match.state === 'live' ? 'En cours' :
             'À venir'}
          </span>
        </div>
        
        {match.scheduled_at && (
          <div className="text-xs text-gray-400">
            {new Date(match.scheduled_at).toLocaleDateString('fr-FR', {
              day: '2-digit',
              month: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
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
            <div className={`font-bold ${match.winner_team_id === match.team_a_id ? 'text-green-400' : 'text-gray-400'}`}>
              {match.score_a}
            </div>
            <div className={`font-bold ${match.winner_team_id === match.team_b_id ? 'text-green-400' : 'text-gray-400'}`}>
              {match.score_b}
            </div>
          </div>
        )}
      </div>
      
      {match.notes && (
        <div className="mt-2 text-xs text-gray-400 italic">
          {match.notes}
        </div>
      )}
    </div>
  );

  const BracketView = () => {
    if (!tournament.bracket || !tournament.bracket.rounds) {
      return (
        <div className="text-center py-8">
          <TrophyIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Bracket non disponible</p>
        </div>
      );
    }

    if (tournament.format === 'rr') {
      // Round Robin - Show standings
      return (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-white">Classement</h3>
          {tournament.bracket.standings && tournament.bracket.standings.length > 0 ? (
            <div className="space-y-2">
              {tournament.bracket.standings.map((standing) => (
                <div key={standing.team_id} className="glass-effect rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="bg-primary-600 text-white text-sm rounded-full w-8 h-8 flex items-center justify-center mr-3">
                      {standing.position}
                    </span>
                    <div>
                      <h4 className="text-white font-medium">{standing.team_name}</h4>
                      <p className="text-gray-400 text-sm">
                        {(standing.win_percentage * 100).toFixed(1)}% de victoires
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">{standing.points} pts</div>
                    <div className="text-gray-400 text-sm">
                      {standing.wins}V - {standing.losses}D
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400">Aucun classement disponible</p>
          )}
        </div>
      );
    }

    // Single/Double Elimination - Show bracket
    const rounds = Object.entries(tournament.bracket.rounds).sort(([a], [b]) => parseInt(a) - parseInt(b));
    
    return (
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white">Bracket {formatTournamentFormat(tournament.format)}</h3>
        <div className="grid gap-6" style={{ gridTemplateColumns: `repeat(${rounds.length}, 1fr)` }}>
          {rounds.map(([roundNum, matches]) => (
            <div key={roundNum} className="space-y-4">
              <h4 className="text-center text-gray-300 font-medium">
                {roundNum === '1' ? 'Premier Tour' : 
                 roundNum === String(tournament.rounds_total) ? 'Finale' :
                 `Round ${roundNum}`}
              </h4>
              <div className="space-y-2">
                {matches.map((match, index) => (
                  <div key={index} className="bg-dark-800 rounded-lg p-3 border border-dark-600">
                    <div className="space-y-1">
                      <div className={`text-sm ${match.winner?.id === match.team_a?.id ? 'text-green-400 font-bold' : 'text-gray-300'}`}>
                        {match.team_a?.name || 'TBD'}
                        {match.score_a !== null && <span className="ml-2">({match.score_a})</span>}
                      </div>
                      <div className={`text-sm ${match.winner?.id === match.team_b?.id ? 'text-green-400 font-bold' : 'text-gray-300'}`}>
                        {match.team_b?.name || 'TBD'}
                        {match.score_b !== null && <span className="ml-2">({match.score_b})</span>}
                      </div>
                    </div>
                    {match.state !== 'pending' && (
                      <div className={`text-xs mt-1 px-2 py-1 rounded ${
                        match.state === 'verified' ? 'bg-green-600' :
                        match.state === 'reported' ? 'bg-yellow-600' :
                        'bg-gray-600'
                      } text-white`}>
                        {match.state === 'verified' ? 'Terminé' :
                         match.state === 'reported' ? 'Reporté' :
                         match.state}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
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
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Nom de l'équipe
            </label>
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
            {actionLoading ? 'Création...' : 'Créer l\'équipe'}
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

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="glass-effect rounded-2xl p-8 mb-8">
          <div className="flex flex-col lg:flex-row">
            {/* Tournament Info */}
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
              
              <h1 className="text-4xl font-bold text-white mb-4 text-shadow">
                {tournament.name}
              </h1>
              
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
                      minute: '2-digit'
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
                {tab === 'bracket' ? 'Bracket' :
                 tab === 'teams' ? `Équipes (${tournament.teams.length})` :
                 tab === 'matches' ? `Matches (${tournament.matches.length})` :
                 tab}
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
                  <h3 className="text-2xl font-bold text-white mb-6">
                    Équipes ({tournament.teams.length})
                  </h3>
                  
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
                {tournament.can_register && isAuthenticated && !tournament.my_team && (
                  <CreateTeamForm />
                )}
                
                {tournament.my_team && (
                  <div className="glass-effect rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-4">Mon équipe</h3>
                    <TeamCard team={tournament.my_team} />
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'matches' && (
            <div className="card p-6">
              <h3 className="text-2xl font-bold text-white mb-6">
                Matches ({tournament.matches.length})
              </h3>
              
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

        {/* Description */}
        <div className="card p-6 mt-6">
          <h3 className="text-2xl font-bold text-white mb-4">Description</h3>
          <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
            {tournament.description}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TournamentDetailPage;