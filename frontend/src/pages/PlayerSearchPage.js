import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  MagnifyingGlassIcon,
  UserPlusIcon,
  UsersIcon,
  TrophyIcon,
  StarIcon,
  CalendarDaysIcon,
  FunnelIcon,
  PlusIcon,
  EyeIcon,
  PencilIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { tournamentService } from '../services/tournamentService';
import { useAuth } from '../App';
import PlayerSearchModal from '../components/PlayerSearchModal';

const PlayerSearchPage = () => {
  const { id: tournamentId } = useParams();
  const [tournament, setTournament] = useState(null);
  const [playerSearches, setPlayerSearches] = useState([]);
  const [mySearch, setMySearch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [filters, setFilters] = useState({
    role: '',
    experience: ''
  });
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (tournamentId) {
      loadTournamentAndSearches();
    }
  }, [tournamentId, filters]);

  const loadTournamentAndSearches = async () => {
    try {
      setLoading(true);
      const [tournamentData, searchesData] = await Promise.all([
        tournamentService.getTournament(tournamentId),
        tournamentService.getPlayerSearches(tournamentId, filters)
      ]);
      
      setTournament(tournamentData);
      setPlayerSearches(searchesData);
      
      if (isAuthenticated) {
        await loadMySearch();
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const loadMySearch = async () => {
    try {
      const mySearches = await tournamentService.getMyPlayerSearches();
      const currentTournamentSearch = mySearches.find(
        search => search.tournament_id === tournamentId && search.is_active
      );
      setMySearch(currentTournamentSearch || null);
    } catch (error) {
      console.error('Failed to load my search:', error);
    }
  };

  const handleCreateSearch = async (searchData) => {
    try {
      setActionLoading(true);
      await tournamentService.createPlayerSearch(tournamentId, searchData);
      toast.success('Recherche d\'équipiers créée avec succès !');
      await loadTournamentAndSearches();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la création de la recherche');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateSearch = async (searchData) => {
    try {
      setActionLoading(true);
      await tournamentService.updatePlayerSearch(mySearch.id, searchData);
      toast.success('Recherche mise à jour avec succès !');
      await loadTournamentAndSearches();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la mise à jour de la recherche');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivateSearch = async () => {
    try {
      setActionLoading(true);
      await tournamentService.deactivatePlayerSearch(mySearch.id);
      toast.success('Recherche désactivée avec succès');
      await loadTournamentAndSearches();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la désactivation de la recherche');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleInvitePlayer = async (playerId) => {
    // This would trigger the team invitation modal
    // For now, just show a message
    toast.info('Fonctionnalité d\'invitation bientôt disponible');
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

  const PlayerSearchCard = ({ search, canInvite = false }) => (
    <div className="glass-effect rounded-lg p-6 mb-4">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {search.user_avatar_url ? (
            <img
              src={search.user_avatar_url}
              alt={search.user_handle}
              className="w-12 h-12 rounded-full"
            />
          ) : (
            <div className="w-12 h-12 bg-dark-600 rounded-full flex items-center justify-center">
              <UsersIcon className="w-6 h-6 text-gray-400" />
            </div>
          )}
          
          <div>
            <h3 className="font-bold text-white text-lg">{search.user_handle}</h3>
            <p className="text-sm text-gray-400">
              Actif depuis {formatDate(search.created_at)}
            </p>
          </div>
        </div>
        
        {canInvite && (
          <button
            onClick={() => handleInvitePlayer(search.user_id)}
            className="btn-primary flex items-center text-sm"
            disabled={actionLoading}
          >
            <UserPlusIcon className="w-4 h-4 mr-1" />
            Inviter
          </button>
        )}
      </div>
      
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {search.preferred_role && (
          <div className="flex items-center">
            <StarIcon className="w-4 h-4 mr-2 text-primary-400" />
            <span className="text-gray-300 text-sm">
              <strong>Rôle préféré:</strong> {search.preferred_role}
            </span>
          </div>
        )}
        
        {search.experience_level && (
          <div className="flex items-center">
            <TrophyIcon className="w-4 h-4 mr-2 text-yellow-400" />
            <span className="text-gray-300 text-sm">
              <strong>Expérience:</strong> {search.experience_level}
            </span>
          </div>
        )}
      </div>
      
      {search.description && (
        <div className="mt-4 p-3 bg-dark-700 rounded border border-dark-600">
          <p className="text-gray-300 text-sm">
            {search.description}
          </p>
        </div>
      )}
    </div>
  );

  if (loading || !tournament) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <MagnifyingGlassIcon className="w-8 h-8 text-primary-400" />
            <h1 className="text-3xl font-bold text-white text-shadow">
              Recherche d'équipiers
            </h1>
          </div>
          <p className="text-xl text-gray-400 mb-4">
            Trouvez des coéquipiers pour le tournoi "{tournament.name}"
          </p>
          
          <div className="flex items-center justify-center space-x-4 text-sm text-gray-400">
            <div className="flex items-center">
              <CalendarDaysIcon className="w-4 h-4 mr-1" />
              {formatDate(tournament.start_at_utc)}
            </div>
            <div className="flex items-center">
              <UsersIcon className="w-4 h-4 mr-1" />
              {tournament.team_size} joueurs/équipe
            </div>
          </div>
        </div>

        {/* Tournament Status Check */}
        {tournament.state !== 'open_registration' && (
          <div className="glass-effect rounded-lg p-4 mb-6 border border-yellow-500/30">
            <div className="flex items-center">
              <XMarkIcon className="w-5 h-5 text-yellow-400 mr-2" />
              <span className="text-yellow-300">
                Les inscriptions sont fermées pour ce tournoi. 
                La recherche d'équipiers n'est plus active.
              </span>
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Search Results */}
          <div className="lg:col-span-2">
            {/* Filters */}
            <div className="glass-effect rounded-lg p-4 mb-6">
              <div className="flex items-center mb-4">
                <FunnelIcon className="w-5 h-5 text-primary-400 mr-2" />
                <h3 className="font-bold text-white">Filtres de recherche</h3>
              </div>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Rôle préféré
                  </label>
                  <input
                    type="text"
                    value={filters.role}
                    onChange={(e) => setFilters({...filters, role: e.target.value})}
                    placeholder="Ex: Pilote, Gunner, Engineer..."
                    className="input-primary w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Niveau d'expérience
                  </label>
                  <input
                    type="text"
                    value={filters.experience}
                    onChange={(e) => setFilters({...filters, experience: e.target.value})}
                    placeholder="Ex: Débutant, Intermédiaire, Expert..."
                    className="input-primary w-full"
                  />
                </div>
              </div>
            </div>

            {/* Results */}
            <div className="glass-effect rounded-lg p-6">
              <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                <UsersIcon className="w-6 h-6 mr-3 text-primary-400" />
                Joueurs recherchant une équipe ({playerSearches.length})
              </h3>
              
              {playerSearches.length > 0 ? (
                <div className="space-y-4">
                  {playerSearches.map((search) => (
                    <PlayerSearchCard 
                      key={search.id} 
                      search={search} 
                      canInvite={tournament.my_team?.can_manage && tournament.state === 'open_registration'}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <MagnifyingGlassIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <h4 className="text-xl font-bold text-white mb-2">Aucun joueur trouvé</h4>
                  <p className="text-gray-400 mb-6">
                    Aucun joueur ne recherche d'équipe pour ce tournoi avec ces critères.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* My Search Status */}
            {isAuthenticated && tournament.state === 'open_registration' && (
              <div className="glass-effect rounded-lg p-6 mb-6">
                <h3 className="text-lg font-bold text-white mb-4">Ma recherche</h3>
                
                {mySearch ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-green-400 font-medium">
                        ✓ Recherche active
                      </span>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setShowEditModal(true)}
                          className="btn-secondary text-sm flex items-center"
                        >
                          <PencilIcon className="w-3 h-3 mr-1" />
                          Modifier
                        </button>
                        <button
                          onClick={handleDeactivateSearch}
                          disabled={actionLoading}
                          className="btn-danger text-sm"
                        >
                          Désactiver
                        </button>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-300 space-y-2">
                      {mySearch.preferred_role && (
                        <div>
                          <strong>Rôle:</strong> {mySearch.preferred_role}
                        </div>
                      )}
                      {mySearch.experience_level && (
                        <div>
                          <strong>Expérience:</strong> {mySearch.experience_level}
                        </div>
                      )}
                      {mySearch.description && (
                        <div>
                          <strong>Description:</strong> {mySearch.description}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center">
                    <p className="text-gray-400 mb-4">
                      Vous ne recherchez pas d'équipe pour ce tournoi.
                    </p>
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="btn-primary flex items-center mx-auto"
                    >
                      <PlusIcon className="w-4 h-4 mr-2" />
                      Créer ma recherche
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tournament Info */}
            <div className="glass-effect rounded-lg p-6">
              <h3 className="text-lg font-bold text-white mb-4">Informations</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center text-gray-300">
                  <TrophyIcon className="w-4 h-4 mr-2 text-primary-400" />
                  <span>
                    {tournament.format === 'se' ? 'Simple Élimination' :
                     tournament.format === 'de' ? 'Double Élimination' :
                     tournament.format === 'rr' ? 'Round Robin' :
                     'Format personnalisé'}
                  </span>
                </div>
                
                <div className="flex items-center text-gray-300">
                  <UsersIcon className="w-4 h-4 mr-2 text-primary-400" />
                  <span>
                    {tournament.team_count}/{tournament.max_teams} équipes inscrites
                  </span>
                </div>

                <div className="pt-3 border-t border-dark-600">
                  <Link 
                    to={`/tournaments/${tournament.id}`}
                    className="text-primary-400 hover:text-primary-300 font-medium"
                  >
                    Retour au tournoi →
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <PlayerSearchModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateSearch}
          isLoading={actionLoading}
          tournament={tournament}
        />
      )}

      {showEditModal && mySearch && (
        <PlayerSearchModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          onSubmit={handleUpdateSearch}
          isLoading={actionLoading}
          tournament={tournament}
          initialData={mySearch}
          isEdit={true}
        />
      )}
    </div>
  );
};

export default PlayerSearchPage;