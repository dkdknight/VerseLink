import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  CalendarDaysIcon,
  MapPinIcon,
  UsersIcon,
  ClockIcon,
  TagIcon,
  DocumentArrowDownIcon,
  UserPlusIcon,
  UserMinusIcon,
  CheckCircleIcon,
  RocketLaunchIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { eventService } from '../services/eventService';
import { useAuth } from '../App';

const EventDetailPage = () => {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const { user, isAuthenticated } = useAuth();

  const canManage =
    isAuthenticated &&
    user &&
    event &&
    (user.id === event.created_by ||
      user.roles?.includes('site_admin') ||
      user.roles?.includes('org_admin'));

  useEffect(() => {
    if (id) {
      loadEvent();
    }
  }, [id]);

  const loadEvent = async () => {
    try {
      setLoading(true);
      const eventData = await eventService.getEvent(id);
      setEvent(eventData);
    } catch (error) {
      console.error('Failed to load event:', error);
      toast.error('Événement non trouvé');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (roleId = null) => {
    if (!isAuthenticated) {
      toast.error('Vous devez être connecté pour vous inscrire');
      return;
    }

    try {
      setActionLoading(true);
      await eventService.signupForEvent(event.id, {
        role_id: roleId,
        notes: '',
        ship_model: ''
      });
      toast.success('Inscription réussie !');
      await loadEvent();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de l\'inscription');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleWithdraw = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir vous désinscrire ?')) {
      return;
    }

    try {
      setActionLoading(true);
      await eventService.withdrawFromEvent(event.id);
      toast.success('Désinscription réussie');
      await loadEvent();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la désinscription');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckin = async () => {
    try {
      setActionLoading(true);
      await eventService.checkinForEvent(event.id);
      toast.success('Check-in réussi !');
      await loadEvent();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors du check-in');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveParticipant = async (userId) => {
    if (!window.confirm('Supprimer ce participant ?')) {
      return;
    }
    try {
      setActionLoading(true);
      await eventService.removeParticipant(event.id, userId);
      toast.success('Participant supprimé');
      await loadEvent();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la suppression');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelEvent = async () => {
    if (!window.confirm("Annuler l'événement ?")) {
      return;
    }
    try {
      setActionLoading(true);
      await eventService.cancelEvent(event.id);
      toast.success("Événement annulé");
      await loadEvent();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("Erreur lors de l'annulation");
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownloadICS = async () => {
    try {
      await eventService.downloadEventICS(event.id);
      toast.success('Calendrier téléchargé');
    } catch (error) {
      toast.error('Erreur lors du téléchargement');
    }
  };

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
      roleplay: 'Roleplay',
      autre: 'Autre'
    };
    return types[type] || type;
  };

  const SignupCard = ({ signup }) => (
    <div className="glass-effect rounded-lg p-4 flex items-center">
      {signup.user_avatar_url ? (
        <img
          src={signup.user_avatar_url}
          alt={signup.user_handle}
          className="w-10 h-10 rounded-full mr-3"
        />
      ) : (
        <div className="w-10 h-10 bg-dark-600 rounded-full flex items-center justify-center mr-3">
          <span className="text-white font-bold text-sm">
            {signup.user_handle.charAt(0).toUpperCase()}
          </span>
        </div>
      )}
      
      <div className="flex-1">
        <div className="flex items-center">
          <h4 className="text-white font-semibold mr-2">{signup.user_handle}</h4>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            signup.status === 'confirmed' 
              ? 'bg-green-100 text-green-800' 
              : signup.status === 'checked_in'
              ? 'bg-blue-100 text-blue-800'
              : signup.status === 'waitlist'
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {signup.status === 'confirmed' ? 'Confirmé' :
             signup.status === 'checked_in' ? 'Présent' :
             signup.status === 'waitlist' ? `Attente #${signup.position_in_waitlist}` :
             signup.status}
          </span>
        </div>
        
        <div className="flex items-center text-gray-400 text-sm">
          {signup.role_name && (
            <>
              <span>{signup.role_name}</span>
              {signup.ship_model && <span className="mx-2">•</span>}
            </>
          )}
          {signup.ship_model && <span>{signup.ship_model}</span>}
        </div>
        
        {signup.notes && (
          <p className="text-gray-400 text-sm mt-1 italic">"{signup.notes}"</p>
        )}
      </div>
      {canManage && signup.user_id !== user?.id && (
        <button
          onClick={() => handleRemoveParticipant(signup.user_id)}
          disabled={actionLoading}
          className="text-red-400 hover:text-red-300 mr-2"
        >
          <UserMinusIcon className="w-5 h-5" />
        </button>
      )}
      <div className="text-right text-xs text-gray-500">
        {new Date(signup.created_at).toLocaleDateString('fr-FR')}
      </div>
    </div>
  );

  if (loading || !event) {
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
            {/* Event Info */}
            <div className="flex-1">
              <div className="flex items-center mb-4">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mr-3 ${getTypeColor(event.type)}`}>
                  {formatEventType(event.type)}
                </span>
                <Link 
                  to={`/organizations/${event.org_id}`}
                  className="text-primary-400 hover:text-primary-300 font-medium"
                >
                  {event.org_name} ({event.org_tag})
                </Link>
              </div>
              
              <h1 className="text-4xl font-bold text-white mb-4 text-shadow">
                {event.title}
              </h1>
              
              <div className="grid md:grid-cols-2 gap-4 mb-6 text-gray-300">
                <div className="flex items-center">
                  <CalendarDaysIcon className="w-5 h-5 mr-2 text-primary-400" />
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
                </div>
                
                <div className="flex items-center">
                  <ClockIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>{event.duration_minutes} minutes</span>
                </div>
                
                {event.location && (
                  <div className="flex items-center">
                    <MapPinIcon className="w-5 h-5 mr-2 text-primary-400" />
                    <span>{event.location}</span>
                  </div>
                )}
                
                <div className="flex items-center">
                  <UsersIcon className="w-5 h-5 mr-2 text-primary-400" />
                  <span>
                    {event.confirmed_count}/{event.max_participants || '∞'} confirmés
                    {event.signup_count > event.confirmed_count && (
                      <span className="text-yellow-400 ml-2">
                        (+{event.signup_count - event.confirmed_count} en attente)
                      </span>
                    )}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Banner */}
            {event.banner_url && (
              <div className="lg:ml-8 mt-6 lg:mt-0">
                <img
                  src={event.banner_url}
                  alt={event.title}
                  className="w-full lg:w-64 h-40 object-cover rounded-xl"
                />
              </div>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex flex-wrap gap-3 mt-6 pt-6 border-t border-dark-600">
            {event.can_signup && (
              <button
                onClick={() => handleSignup()}
                disabled={actionLoading || event.is_full}
                className="btn-primary flex items-center"
              >
                <UserPlusIcon className="w-5 h-5 mr-2" />
                {actionLoading ? 'Inscription...' : 'S\'inscrire'}
              </button>
            )}
            
            {event.my_signup && event.my_signup.status !== 'withdrawn' && (
              <>
                {event.can_checkin && (
                  <button
                    onClick={handleCheckin}
                    disabled={actionLoading}
                    className="btn-primary flex items-center bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircleIcon className="w-5 h-5 mr-2" />
                    {actionLoading ? 'Check-in...' : 'Check-in'}
                  </button>
                )}
                
                <button
                  onClick={handleWithdraw}
                  disabled={actionLoading}
                  className="btn-ghost flex items-center text-red-400 hover:text-red-300 border-red-400 hover:border-red-300"
                >
                  <UserMinusIcon className="w-5 h-5 mr-2" />
                  {actionLoading ? 'Désinscription...' : 'Se désinscrire'}
                </button>
              </>
            )}
            
            <button
              onClick={handleDownloadICS}
              className="btn-secondary flex items-center"
            >
              <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
              Télécharger .ics
            </button>
            
            {canManage && (
              <>
                <Link
                  to={`/events/${event.id}/edit`}
                  className="btn-secondary flex items-center"
                >
                  Modifier l'événement
                </Link>
                {event.state !== 'cancelled' && (
                  <button
                    onClick={handleCancelEvent}
                    disabled={actionLoading}
                    className="btn-ghost flex items-center text-red-400 hover:text-red-300 border-red-400 hover:border-red-300"
                  >
                    <XCircleIcon className="w-5 h-5 mr-2" />
                    {actionLoading ? 'Annulation...' : 'Annuler'}
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Description */}
          <div className="lg:col-span-2">
            <div className="card p-6 mb-6">
              <h3 className="text-2xl font-bold text-white mb-4">Description</h3>
              <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {event.description}
              </div>
            </div>
            
            {/* Fleet */}
            {event.fleet_ships && event.fleet_ships.length > 0 && (
              <div className="card p-6 mb-6">
                <h3 className="text-2xl font-bold text-white mb-4">
                  Manifeste de la Flotte
                </h3>
                
                <div className="grid gap-4">
                  {event.fleet_ships.map((ship) => (
                    <div key={ship.id} className="glass-effect rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-white font-semibold flex items-center">
                            <RocketLaunchIcon className="w-5 h-5 mr-2 text-primary-400" />
                            {ship.ship_model}
                          </h4>
                          <p className="text-gray-400 text-sm">
                            Équipage requis: {ship.required_crew} personne{ship.required_crew > 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      {ship.notes && (
                        <p className="text-gray-400 text-sm mt-2 italic">
                          {ship.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Roles */}
            {event.roles && event.roles.length > 0 && (
              <div className="card p-6 mb-6">
                <h3 className="text-xl font-bold text-white mb-4">
                  Rôles Disponibles
                </h3>
                
                <div className="space-y-3">
                  {event.roles.map((role) => (
                    <div key={role.id} className="glass-effect rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-white font-medium">{role.name}</h4>
                        <span className={`text-sm px-2 py-1 rounded ${
                          role.is_full ? 'bg-red-600 text-white' : 'bg-green-600 text-white'
                        }`}>
                          {role.current_signups}/{role.capacity}
                        </span>
                      </div>
                      
                      {role.description && (
                        <p className="text-gray-400 text-sm mb-2">{role.description}</p>
                      )}
                      
                      {role.waitlist_count > 0 && (
                        <p className="text-yellow-400 text-sm">
                          {role.waitlist_count} en attente
                        </p>
                      )}
                      
                      {event.can_signup && !event.my_signup && (
                        <button
                          onClick={() => handleSignup(role.id)}
                          disabled={actionLoading}
                          className="btn-primary w-full mt-2 text-sm py-1"
                        >
                          S'inscrire pour ce rôle
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* My Signup Status */}
            {event.my_signup && (
              <div className="card p-6 mb-6">
                <h3 className="text-xl font-bold text-white mb-4">Mon Inscription</h3>
                <SignupCard signup={event.my_signup} />
              </div>
            )}
          </div>
        </div>

        {/* Participants */}
        {event.signups && event.signups.length > 0 && (
          <div className="card p-6 mt-6">
            <h3 className="text-2xl font-bold text-white mb-6">
              Participants ({event.signups.length})
            </h3>
            
            <div className="grid gap-4">
              {event.signups.map((signup) => (
                <SignupCard key={signup.id} signup={signup} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EventDetailPage;