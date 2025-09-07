import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  UsersIcon,
  CalendarDaysIcon,
  TrophyIcon,
  LinkIcon,
  UserPlusIcon,
  UserMinusIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { organizationService } from '../services/organizationService';
import { useAuth } from '../App';

const OrganizationDetailPage = () => {
  const { id } = useParams();
  const [organization, setOrganization] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [isMember, setIsMember] = useState(false);
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (id) {
      loadOrganization();
      loadMembers();
    }
  }, [id]);

  useEffect(() => {
    if (user && members.length > 0) {
      setIsMember(members.some(member => member.user_id === user.id));
    }
  }, [user, members]);

  const loadOrganization = async () => {
    try {
      const org = await organizationService.getOrganization(id);
      setOrganization(org);
    } catch (error) {
      console.error('Failed to load organization:', error);
      toast.error('Organisation non trouvée');
    }
  };

  const loadMembers = async () => {
    try {
      setLoading(true);
      const orgMembers = await organizationService.getMembers(id);
      setMembers(orgMembers);
    } catch (error) {
      console.error('Failed to load members:', error);
      toast.error('Erreur lors du chargement des membres');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!isAuthenticated) {
      toast.error('Vous devez être connecté pour rejoindre une organisation');
      return;
    }

    try {
      setJoining(true);
      await organizationService.joinOrganization(id);
      toast.success('Vous avez rejoint l\'organisation !');
      
      // Refresh data
      await loadOrganization();
      await loadMembers();
    } catch (error) {
      console.error('Failed to join organization:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de l\'adhésion');
      }
    } finally {
      setJoining(false);
    }
  };

  const handleLeave = async () => {
    if (!user) return;

    if (!window.confirm('Êtes-vous sûr de vouloir quitter cette organisation ?')) {
      return;
    }

    try {
      setLeaving(true);
      await organizationService.leaveOrganization(id, user.id);
      toast.success('Vous avez quitté l\'organisation');
      
      // Refresh data
      await loadOrganization();
      await loadMembers();
    } catch (error) {
      console.error('Failed to leave organization:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors du départ');
      }
    } finally {
      setLeaving(false);
    }
  };

  const MemberCard = ({ member }) => (
    <div className="glass-effect rounded-lg p-4 flex items-center">
      {member.avatar_url ? (
        <img
          src={member.avatar_url}
          alt={member.handle}
          className="w-12 h-12 rounded-full mr-4"
        />
      ) : (
        <div className="w-12 h-12 bg-dark-600 rounded-full flex items-center justify-center mr-4">
          <span className="text-white font-bold">
            {member.handle.charAt(0).toUpperCase()}
          </span>
        </div>
      )}
      
      <div className="flex-1">
        <h4 className="text-white font-semibold">{member.handle}</h4>
        <p className="text-gray-400 text-sm">{member.discord_username}</p>
      </div>
      
      <div className="text-right">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          member.role === 'admin' 
            ? 'bg-red-100 text-red-800' 
            : member.role === 'staff'
            ? 'bg-yellow-100 text-yellow-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {member.role === 'admin' ? 'Admin' : 
           member.role === 'staff' ? 'Staff' : 'Membre'}
        </span>
        <p className="text-xs text-gray-500 mt-1">
          Rejoint le {new Date(member.joined_at).toLocaleDateString('fr-FR')}
        </p>
      </div>
    </div>
  );

  if (loading || !organization) {
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
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between">
            <div className="flex items-center mb-6 lg:mb-0">
              <div className="w-20 h-20 bg-gradient-star rounded-xl flex items-center justify-center mr-6">
                <span className="text-white font-bold text-2xl">{organization.tag}</span>
              </div>
              
              <div>
                <h1 className="text-4xl font-bold text-white mb-2 text-shadow">
                  {organization.name}
                </h1>
                <div className="flex items-center space-x-4">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    organization.visibility === 'public' 
                      ? 'bg-green-100 text-green-800' 
                      : organization.visibility === 'unlisted'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {organization.visibility === 'public' ? 'Publique' : 
                     organization.visibility === 'unlisted' ? 'Non listée' : 'Privée'}
                  </span>
                  
                  {organization.website_url && (
                    <a
                      href={organization.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center text-primary-400 hover:text-primary-300 text-sm"
                    >
                      <LinkIcon className="w-4 h-4 mr-1" />
                      Site web
                    </a>
                  )}
                </div>
              </div>
            </div>

            {/* Join/Leave Button */}
            {isAuthenticated && (
              <div className="flex space-x-3">
                <Link
                  to={`/organizations/${id}/events/new`}
                  className="btn-primary flex items-center"
                >
                  <PlusIcon className="w-5 h-5 mr-2" />
                  Créer un événement
                </Link>
                {isMember ? (
                  <button
                    onClick={handleLeave}
                    disabled={leaving}
                    className="btn-ghost flex items-center text-red-400 hover:text-red-300 border-red-400 hover:border-red-300"
                  >
                    <UserMinusIcon className="w-5 h-5 mr-2" />
                    {leaving ? 'Départ...' : 'Quitter'}
                  </button>
                ) : (
                  <button
                    onClick={handleJoin}
                    disabled={joining || organization.visibility === 'private'}
                    className="btn-primary flex items-center"
                  >
                    <UserPlusIcon className="w-5 h-5 mr-2" />
                    {joining ? 'Adhésion...' : 'Rejoindre'}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Description */}
          {organization.description && (
            <div className="mt-6 pt-6 border-t border-dark-600">
              <p className="text-gray-300 leading-relaxed">
                {organization.description}
              </p>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Stats */}
          <div className="lg:col-span-1">
            <div className="card p-6 mb-6">
              <h3 className="text-xl font-bold text-white mb-4">Statistiques</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <UsersIcon className="w-5 h-5 text-primary-400 mr-2" />
                    <span className="text-gray-300">Membres</span>
                  </div>
                  <span className="text-white font-bold">{organization.member_count}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <CalendarDaysIcon className="w-5 h-5 text-accent-green mr-2" />
                    <span className="text-gray-300">Événements</span>
                  </div>
                  <span className="text-white font-bold">{organization.event_count}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <TrophyIcon className="w-5 h-5 text-accent-gold mr-2" />
                    <span className="text-gray-300">Tournois</span>
                  </div>
                  <span className="text-white font-bold">{organization.tournament_count}</span>
                </div>
              </div>
            </div>

            {/* Organization Info */}
            <div className="card p-6">
              <h3 className="text-xl font-bold text-white mb-4">Informations</h3>
              
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-400">Créée le :</span>
                  <div className="text-white">
                    {new Date(organization.created_at).toLocaleDateString('fr-FR')}
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-400">Tag :</span>
                  <div className="text-white font-mono">{organization.tag}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Members */}
          <div className="lg:col-span-2">
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-white">
                  Membres ({members.length})
                </h3>
              </div>

              {members.length > 0 ? (
                <div className="grid gap-4">
                  {members.map((member) => (
                    <MemberCard key={member.user_id} member={member} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <UsersIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">Aucun membre trouvé</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganizationDetailPage;