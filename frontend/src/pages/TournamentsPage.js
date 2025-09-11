import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  TrophyIcon,
  MagnifyingGlassIcon,
  CalendarDaysIcon,
  UsersIcon,
  TagIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';
import { getMediaUrl } from '../utils/media';

const TournamentsPage = () => {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [formatFilter, setFormatFilter] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    loadTournaments();
  }, [searchQuery, formatFilter, stateFilter]);

  const loadTournaments = async () => {
    try {
      setLoading(true);
      const params = {};
      if (searchQuery) params.query = searchQuery;
      if (formatFilter) params.format = formatFilter;
      if (stateFilter) params.state = stateFilter;
      
      const tournamentsData = await tournamentService.listTournaments(params);
      setTournaments(tournamentsData);
    } catch (error) {
      console.error('Failed to load tournaments:', error);
      toast.error('Erreur lors du chargement des tournois');
    } finally {
      setLoading(false);
    }
  };

  const TournamentCard = ({ tournament }) => (
    <Link 
      to={`/tournaments/${tournament.slug}`}
      className="card-hover p-6 block transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center mb-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mr-2 ${getFormatColor(tournament.format)}`}>
              {formatTournamentFormat(tournament.format)}
            </span>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStateColor(tournament.state)}`}>
              {formatTournamentState(tournament.state)}
            </span>
          </div>
          <h3 className="text-white font-bold text-xl mb-2">{tournament.name}</h3>
          <p className="text-gray-400 text-sm line-clamp-2 mb-3">
            {tournament.description}
          </p>
        </div>
        {tournament.banner_url && (
          <img
            src={getMediaUrl(tournament.banner_url)}
            alt={tournament.name}
            className="w-20 h-16 object-cover rounded-lg ml-4"
          />
        )}
      </div>

      {/* Tournament Info */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-gray-300 text-sm">
          <CalendarDaysIcon className="w-4 h-4 mr-2" />
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
        
        <div className="flex items-center text-gray-300 text-sm">
          <TagIcon className="w-4 h-4 mr-2" />
          <span>{tournament.org_name} ({tournament.org_tag})</span>
        </div>
        
        <div className="flex items-center text-gray-300 text-sm">
          <UsersIcon className="w-4 h-4 mr-2" />
          <span>
            {tournament.team_count}/{tournament.max_teams} équipes
            <span className="mx-2">•</span>
            {tournament.team_size} joueurs/équipe
          </span>
        </div>
      </div>

      {/* Prize and Status */}
      <div className="flex items-center justify-between">
        <div>
          {tournament.prize_pool && (
            <div className="text-accent-gold font-medium text-sm">
              🏆 {tournament.prize_pool}
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {tournament.is_registration_open && (
            <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">
              Inscriptions ouvertes
            </span>
          )}
          {tournament.state === 'ongoing' && (
            <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded flex items-center">
              <PlayIcon className="w-3 h-3 mr-1" />
              En cours
            </span>
          )}
          {tournament.state === 'finished' && tournament.winner_team_name && (
            <span className="text-xs bg-yellow-600 text-white px-2 py-1 rounded flex items-center">
              <TrophyIcon className="w-3 h-3 mr-1" />
              {tournament.winner_team_name}
            </span>
          )}
        </div>
      </div>
    </Link>
  );

  const getFormatColor = (format) => {
    const colors = {
      se: 'bg-red-100 text-red-800',
      de: 'bg-purple-100 text-purple-800',
      rr: 'bg-blue-100 text-blue-800',
      swiss: 'bg-green-100 text-green-800'
    };
    return colors[format] || 'bg-gray-100 text-gray-800';
  };

  const getStateColor = (state) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      open_registration: 'bg-green-100 text-green-800',
      registration_closed: 'bg-yellow-100 text-yellow-800',
      ongoing: 'bg-blue-100 text-blue-800',
      finished: 'bg-purple-100 text-purple-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[state] || 'bg-gray-100 text-gray-800';
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

  const tournamentFormats = [
    { value: '', label: 'Tous les formats' },
    { value: 'se', label: 'Simple Élimination' },
    { value: 'de', label: 'Double Élimination' },
    { value: 'rr', label: 'Round Robin' },
    { value: 'swiss', label: 'Système Suisse' }
  ];

  const tournamentStates = [
    { value: '', label: 'Tous les états' },
    { value: 'open_registration', label: 'Inscriptions ouvertes' },
    { value: 'ongoing', label: 'En cours' },
    { value: 'finished', label: 'Terminés' }
  ];

  const LoadingSkeleton = () => (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex space-x-2 mb-2">
            <div className="h-5 bg-dark-600 rounded skeleton w-20"></div>
            <div className="h-5 bg-dark-600 rounded skeleton w-24"></div>
          </div>
          <div className="h-6 bg-dark-600 rounded skeleton mb-2"></div>
          <div className="h-16 bg-dark-600 rounded skeleton mb-3"></div>
        </div>
        <div className="w-20 h-16 bg-dark-600 rounded-lg skeleton ml-4"></div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="h-4 bg-dark-600 rounded skeleton"></div>
        <div className="h-4 bg-dark-600 rounded skeleton w-3/4"></div>
        <div className="h-4 bg-dark-600 rounded skeleton w-1/2"></div>
      </div>
      
      <div className="flex justify-between">
        <div className="h-4 bg-dark-600 rounded skeleton w-24"></div>
        <div className="h-4 bg-dark-600 rounded skeleton w-16"></div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4 text-shadow">
            Tournois Star Citizen
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Participez aux compétitions organisées par la communauté et prouvez votre valeur
          </p>
        </div>

        {isAuthenticated && (
          <div className="mb-8 text-right">
            <Link to="/tournaments/new" className="btn-primary inline-flex items-center">
              <PlusIcon className="w-5 h-5 mr-2" />
              Créer un tournoi
            </Link>
          </div>
        )}

        {/* Search and Filters */}
        <div className="glass-effect rounded-xl p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par nom ou description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-primary w-full pl-10"
              />
            </div>

            {/* Format Filter */}
            <select
              value={formatFilter}
              onChange={(e) => setFormatFilter(e.target.value)}
              className="input-primary w-full lg:w-48"
            >
              {tournamentFormats.map(format => (
                <option key={format.value} value={format.value}>{format.label}</option>
              ))}
            </select>

            {/* State Filter */}
            <select
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
              className="input-primary w-full lg:w-48"
            >
              {tournamentStates.map(state => (
                <option key={state.value} value={state.value}>{state.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <LoadingSkeleton key={i} />
            ))}
          </div>
        ) : tournaments.length > 0 ? (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                {tournaments.length} tournoi{tournaments.length > 1 ? 's' : ''} trouvé{tournaments.length > 1 ? 's' : ''}
              </h2>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tournaments.map((tournament) => (
                <TournamentCard key={tournament.id} tournament={tournament} />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <TrophyIcon className="w-24 h-24 text-gray-600 mx-auto mb-6" />
            <h3 className="text-2xl font-bold text-white mb-4">Aucun tournoi trouvé</h3>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              {searchQuery || formatFilter || stateFilter
                ? "Essayez de modifier vos critères de recherche ou vos filtres."
                : "Aucun tournoi organisé pour le moment."
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TournamentsPage;