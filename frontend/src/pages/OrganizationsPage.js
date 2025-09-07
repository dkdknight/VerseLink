import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  MagnifyingGlassIcon,
  PlusIcon,
  UsersIcon,
  CalendarDaysIcon,
  TrophyIcon
} from '@heroicons/react/24/outline';
import { organizationService } from '../services/organizationService';
import { useAuth } from '../App';

const OrganizationsPage = () => {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibilityFilter, setVisibilityFilter] = useState('');
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    loadOrganizations();
  }, [searchQuery, visibilityFilter]);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const orgs = await organizationService.listOrganizations(
        searchQuery, 
        visibilityFilter || null, 
        20, 
        0
      );
      setOrganizations(orgs);
    } catch (error) {
      console.error('Failed to load organizations:', error);
      toast.error('Erreur lors du chargement des organisations');
    } finally {
      setLoading(false);
    }
  };

  const OrganizationCard = ({ org }) => (
    <Link 
      to={`/organizations/${org.id}`}
      className="card-hover p-6 block transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-gradient-star rounded-lg flex items-center justify-center mr-4">
            <span className="text-white font-bold text-lg">{org.tag}</span>
          </div>
          <div>
            <h3 className="text-white font-bold text-xl">{org.name}</h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              org.visibility === 'public' 
                ? 'bg-green-100 text-green-800' 
                : org.visibility === 'unlisted'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {org.visibility === 'public' ? 'Publique' : 
               org.visibility === 'unlisted' ? 'Non listée' : 'Privée'}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-gray-400 text-sm mb-4 line-clamp-3">
        {org.description || 'Aucune description disponible.'}
      </p>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="glass-effect rounded-lg p-3">
          <UsersIcon className="w-5 h-5 text-primary-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{org.member_count}</div>
          <div className="text-xs text-gray-400">Membres</div>
        </div>
        <div className="glass-effect rounded-lg p-3">
          <CalendarDaysIcon className="w-5 h-5 text-accent-green mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{org.event_count}</div>
          <div className="text-xs text-gray-400">Événements</div>
        </div>
        <div className="glass-effect rounded-lg p-3">
          <TrophyIcon className="w-5 h-5 text-accent-gold mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{org.tournament_count}</div>
          <div className="text-xs text-gray-400">Tournois</div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-dark-600 flex items-center justify-between">
        <span className="text-xs text-gray-500">
          Créée le {new Date(org.created_at).toLocaleDateString('fr-FR')}
        </span>
        {org.website_url && (
          <span className="text-xs text-primary-400">
            Site web disponible
          </span>
        )}
      </div>
    </Link>
  );

  const LoadingSkeleton = () => (
    <div className="card p-6">
      <div className="flex items-center mb-4">
        <div className="w-12 h-12 bg-dark-600 rounded-lg mr-4 skeleton"></div>
        <div className="flex-1">
          <div className="h-6 bg-dark-600 rounded skeleton mb-2"></div>
          <div className="h-4 bg-dark-600 rounded skeleton w-20"></div>
        </div>
      </div>
      <div className="h-16 bg-dark-600 rounded skeleton mb-4"></div>
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass-effect rounded-lg p-3">
            <div className="w-5 h-5 bg-dark-600 rounded skeleton mx-auto mb-1"></div>
            <div className="h-6 bg-dark-600 rounded skeleton mb-1"></div>
            <div className="h-3 bg-dark-600 rounded skeleton"></div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4 text-shadow">
            Organisations Star Citizen
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Découvrez et rejoignez les corporations les plus actives de la communauté
          </p>
        </div>

        {/* Search and Filters */}
        <div className="glass-effect rounded-xl p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par nom, tag ou description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-primary w-full pl-10"
              />
            </div>

            {/* Visibility Filter */}
            <select
              value={visibilityFilter}
              onChange={(e) => setVisibilityFilter(e.target.value)}
              className="input-primary w-full lg:w-48"
            >
              <option value="">Toutes les visibilités</option>
              <option value="public">Publiques</option>
              <option value="unlisted">Non listées</option>
            </select>

            {/* Create Organization Button */}
            {isAuthenticated && (
              <Link
                to="/organizations/create"
                className="btn-primary flex items-center justify-center whitespace-nowrap"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Créer une Organisation
              </Link>
            )}
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <LoadingSkeleton key={i} />
            ))}
          </div>
        ) : organizations.length > 0 ? (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                {organizations.length} organisation{organizations.length > 1 ? 's' : ''} trouvée{organizations.length > 1 ? 's' : ''}
              </h2>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {organizations.map((org) => (
                <OrganizationCard key={org.id} org={org} />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <UsersIcon className="w-24 h-24 text-gray-600 mx-auto mb-6" />
            <h3 className="text-2xl font-bold text-white mb-4">Aucune organisation trouvée</h3>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              {searchQuery || visibilityFilter 
                ? "Essayez de modifier vos critères de recherche ou vos filtres."
                : "Soyez le premier à créer une organisation !"
              }
            </p>
            {isAuthenticated && !searchQuery && !visibilityFilter && (
              <Link to="/organizations/create" className="btn-primary">
                Créer la première organisation
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrganizationsPage;