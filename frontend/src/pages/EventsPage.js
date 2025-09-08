import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  CalendarDaysIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  UsersIcon,
  ClockIcon,
  TagIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { eventService } from '../services/eventService';
import { useAuth } from '../App';

const EventsPage = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [orgFilter, setOrgFilter] = useState('');
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    loadEvents();
  }, [searchQuery, typeFilter, orgFilter]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params = { start_date: new Date().toISOString() };
      if (searchQuery) params.query = searchQuery;
      if (typeFilter) params.type = typeFilter;
      if (orgFilter) params.org_id = orgFilter;
      
      const eventsData = await eventService.listEvents(params);
      setEvents(eventsData);
    } catch (error) {
      console.error('Failed to load events:', error);
      toast.error('Erreur lors du chargement des événements');
    } finally {
      setLoading(false);
    }
  };

  const EventCard = ({ event }) => (
    <Link 
      to={`/events/${event.slug}`}
      className="card-hover p-6 block transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center mb-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mr-2 ${getTypeColor(event.type)}`}>
              {formatEventType(event.type)}
            </span>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStateColor(event.state)}`}>
              {formatEventState(event.state)}
            </span>
          </div>
          <h3 className="text-white font-bold text-xl mb-2">{event.title}</h3>
          <p className="text-gray-400 text-sm line-clamp-2 mb-3">
            {event.description}
          </p>
        </div>
        {event.banner_url && (
          <img
            src={event.banner_url}
            alt={event.title}
            className="w-20 h-16 object-cover rounded-lg ml-4"
          />
        )}
      </div>

      {/* Event Info */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-gray-300 text-sm">
          <CalendarDaysIcon className="w-4 h-4 mr-2" />
          <span>
            {new Date(event.start_at_utc).toLocaleDateString('fr-FR', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
          <span className="mx-2">•</span>
          <ClockIcon className="w-4 h-4 mr-1" />
          <span>{event.duration_minutes}min</span>
        </div>
        
        {event.location && (
          <div className="flex items-center text-gray-300 text-sm">
            <MapPinIcon className="w-4 h-4 mr-2" />
            <span>{event.location}</span>
          </div>
        )}
        
        <div className="flex items-center text-gray-300 text-sm">
          <TagIcon className="w-4 h-4 mr-2" />
          <span>{event.org_name} ({event.org_tag})</span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center text-primary-400">
            <UsersIcon className="w-4 h-4 mr-1" />
            <span className="text-sm font-medium">
              {event.confirmed_count}/{event.max_participants || '∞'} confirmés
            </span>
          </div>
          {event.signup_count > event.confirmed_count && (
            <div className="flex items-center text-yellow-400">
              <span className="text-sm font-medium">
                +{event.signup_count - event.confirmed_count} en attente
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {event.is_full && (
            <span className="text-xs bg-red-600 text-white px-2 py-1 rounded">
              Complet
            </span>
          )}
          {event.checkin_available && (
            <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">
              Check-in ouvert
            </span>
          )}
        </div>
      </div>
    </Link>
  );

  const getTypeColor = (type) => {
    const colors = {
      raid: 'bg-red-100 text-red-800',
      course: 'bg-blue-100 text-blue-800',
      pvp: 'bg-purple-100 text-purple-800',
      fps: 'bg-orange-100 text-orange-800',
      salvaging: 'bg-yellow-100 text-yellow-800',
      logistique: 'bg-green-100 text-green-800',
      exploration: 'bg-indigo-100 text-indigo-800',
      mining: 'bg-amber-100 text-amber-800',
      trading: 'bg-emerald-100 text-emerald-800',
      roleplay: 'bg-pink-100 text-pink-800',
      autre: 'bg-gray-100 text-gray-800'
    };
    return colors[type] || colors.autre;
  };

  const getStateColor = (state) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      published: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      completed: 'bg-blue-100 text-blue-800'
    };
    return colors[state] || colors.published;
  };

  const formatEventType = (type) => {
    const types = {
      raid: 'Raid',
      course: 'Course',
      pvp: 'PvP',
      fps: 'FPS',
      salvaging: 'Salvage',
      logistique: 'Logistique',
      exploration: 'Exploration',
      mining: 'Mining',
      trading: 'Commerce',
      roleplay: 'RP',
      autre: 'Autre'
    };
    return types[type] || type;
  };

  const formatEventState = (state) => {
    const states = {
      draft: 'Brouillon',
      published: 'Publié',
      cancelled: 'Annulé',
      completed: 'Terminé'
    };
    return states[state] || state;
  };

  const eventTypes = [
    { value: '', label: 'Tous les types' },
    { value: 'raid', label: 'Raid' },
    { value: 'course', label: 'Course' },
    { value: 'pvp', label: 'PvP' },
    { value: 'fps', label: 'FPS' },
    { value: 'salvaging', label: 'Salvage' },
    { value: 'logistique', label: 'Logistique' },
    { value: 'exploration', label: 'Exploration' },
    { value: 'mining', label: 'Mining' },
    { value: 'trading', label: 'Commerce' },
    { value: 'roleplay', label: 'Roleplay' },
    { value: 'autre', label: 'Autre' }
  ];

  const LoadingSkeleton = () => (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex space-x-2 mb-2">
            <div className="h-5 bg-dark-600 rounded skeleton w-16"></div>
            <div className="h-5 bg-dark-600 rounded skeleton w-20"></div>
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
            Événements Star Citizen
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Découvrez et participez aux événements organisés par la communauté
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
                placeholder="Rechercher par titre, description ou lieu..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-primary w-full pl-10"
              />
            </div>

            {/* Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="input-primary w-full lg:w-48"
            >
              {eventTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
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
        ) : events.length > 0 ? (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                {events.length} événement{events.length > 1 ? 's' : ''} trouvé{events.length > 1 ? 's' : ''}
              </h2>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {events.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <CalendarDaysIcon className="w-24 h-24 text-gray-600 mx-auto mb-6" />
            <h3 className="text-2xl font-bold text-white mb-4">Aucun événement trouvé</h3>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              {searchQuery || typeFilter 
                ? "Essayez de modifier vos critères de recherche ou vos filtres."
                : "Aucun événement publié pour le moment."
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EventsPage;