import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  PencilIcon,
  PhotoIcon,
  UsersIcon,
  TrashIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { organizationService } from '../services/organizationService';
import { useAuth } from '../App';

const ManageOrganizationPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [organization, setOrganization] = useState(null);
  const [members, setMembers] = useState([]);
  const [joinRequests, setJoinRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [selectedNewOwner, setSelectedNewOwner] = useState('');
  
  // Form states
  const [profileForm, setProfileForm] = useState({
    name: '',
    description: '',
    website_url: '',
    discord_url: '',
    twitter_url: '',
    youtube_url: '',
    twitch_url: '',
    visibility: 'public',
    membership_policy: 'open'
  });

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [orgData, membersData] = await Promise.all([
        organizationService.getOrganization(id),
        organizationService.getMembers(id)
      ]);
      
      setOrganization(orgData);
      setMembers(membersData);
      
      // Initialize form with current data
      setProfileForm({
        name: orgData.name || '',
        description: orgData.description || '',
        website_url: orgData.website_url || '',
        discord_url: orgData.discord_url || '',
        twitter_url: orgData.twitter_url || '',
        youtube_url: orgData.youtube_url || '',
        twitch_url: orgData.twitch_url || '',
        visibility: orgData.visibility || 'public',
        membership_policy: orgData.membership_policy || 'open'
      });
      
      // Load join requests if needed
      if (orgData.membership_policy === 'request_only') {
        loadJoinRequests();
      }
    } catch (error) {
      console.error('Failed to load organization data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const loadJoinRequests = async () => {
    try {
      const requests = await organizationService.getJoinRequests(id);
      setJoinRequests(requests);
    } catch (error) {
      console.error('Failed to load join requests:', error);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      const updatedOrg = await organizationService.updateOrganization(id, profileForm);
      setOrganization(updatedOrg);
      toast.success('Profil mis à jour');
    } catch (error) {
      console.error('Failed to update organization:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleJoinRequestAction = async (requestId, action) => {
    try {
      await organizationService.processJoinRequest(id, requestId, action);
      toast.success(action === 'accepted' ? 'Demande acceptée' : 'Demande refusée');
      loadJoinRequests();
      if (action === 'accepted') {
        loadData(); // Refresh member count
      }
    } catch (error) {
      console.error('Failed to process join request:', error);
      toast.error('Erreur lors du traitement de la demande');
    }
  };

  const handleMemberRoleChange = async (memberId, newRole) => {
    try {
      await organizationService.updateMemberRole(id, memberId, newRole);
      toast.success('Rôle mis à jour');
      loadData();
    } catch (error) {
      console.error('Failed to update member role:', error);
      toast.error('Erreur lors de la mise à jour du rôle');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir retirer ce membre ?')) {
      return;
    }
    
    try {
      await organizationService.removeMember(id, memberId);
      toast.success('Membre retiré');
      loadData();
    } catch (error) {
      console.error('Failed to remove member:', error);
      toast.error('Erreur lors du retrait du membre');
    }
  };

  const handleTransferOwnership = async () => {
    if (!selectedNewOwner) return;
    
    try {
      await organizationService.transferOwnership(id, selectedNewOwner);
      toast.success('Propriété transférée');
      setShowTransferModal(false);
      navigate(`/organizations/${id}`);
    } catch (error) {
      console.error('Failed to transfer ownership:', error);
      toast.error('Erreur lors du transfert de propriété');
    }
  };

  const handleDeleteOrganization = async () => {
    try {
      await organizationService.deleteOrganization(id);
      toast.success('Organisation supprimée');
      setShowDeleteModal(false);
      navigate('/organizations');
    } catch (error) {
      console.error('Failed to delete organization:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Le fichier ne doit pas dépasser 10MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Seules les images sont acceptées');
      return;
    }

    try {
      const response = await organizationService.uploadLogo(id, file);
      toast.success('Logo téléchargé avec succès');
      // Refresh organization data
      loadData();
    } catch (error) {
      console.error('Failed to upload logo:', error);
      toast.error('Erreur lors du téléchargement du logo');
    }
  };

  const handleBannerUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Le fichier ne doit pas dépasser 10MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Seules les images sont acceptées');
      return;
    }

    try {
      const response = await organizationService.uploadBanner(id, file);
      toast.success('Bannière téléchargée avec succès');
      // Refresh organization data
      loadData();
    } catch (error) {
      console.error('Failed to upload banner:', error);
      toast.error('Erreur lors du téléchargement de la bannière');
    }
  };

  const isOwner = user && organization && user.id === organization.owner_id;
  const isAdmin = members.find(m => m.user_id === user?.id)?.role === 'admin' || isOwner;
  const isModerator = members.find(m => m.user_id === user?.id)?.role === 'moderator' || isAdmin;

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Organisation non trouvée</h1>
          <button onClick={() => navigate('/organizations')} className="btn-primary">
            Retour aux organisations
          </button>
        </div>
      </div>
    );
  }

  if (!isModerator) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-4">Accès refusé</h1>
          <p className="text-gray-400 mb-8">Vous n'avez pas les permissions pour gérer cette organisation.</p>
          <button onClick={() => navigate(`/organizations/${id}`)} className="btn-primary">
            Voir l'organisation
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'profile', name: 'Profil', icon: PencilIcon, visible: isAdmin },
    { id: 'media', name: 'Médias', icon: PhotoIcon, visible: isAdmin },
    { id: 'members', name: 'Membres', icon: UsersIcon, visible: isModerator },
    { id: 'requests', name: 'Demandes', icon: CheckCircleIcon, visible: isModerator && organization.membership_policy === 'request_only' },
    { id: 'danger', name: 'Zone de danger', icon: ExclamationTriangleIcon, visible: isOwner }
  ].filter(tab => tab.visible);

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="glass-effect rounded-2xl p-8 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                Gérer {organization.name}
              </h1>
              <p className="text-gray-400">
                Administrez votre organisation et ses membres
              </p>
            </div>
            <button
              onClick={() => navigate(`/organizations/${id}`)}
              className="btn-ghost"
            >
              Voir l'organisation
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="card p-6 mb-8">
          <div className="border-b border-dark-600 mb-8">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="w-5 h-5 mr-2" />
                  {tab.name}
                  {tab.id === 'requests' && joinRequests.length > 0 && (
                    <span className="ml-2 bg-primary-500 text-white text-xs rounded-full px-2 py-1">
                      {joinRequests.length}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'profile' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-6">Informations du profil</h2>
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Nom de l'organisation *
                    </label>
                    <input
                      type="text"
                      value={profileForm.name}
                      onChange={(e) => setProfileForm({...profileForm, name: e.target.value})}
                      className="input-primary w-full"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Visibilité
                    </label>
                    <select
                      value={profileForm.visibility}
                      onChange={(e) => setProfileForm({...profileForm, visibility: e.target.value})}
                      className="input-primary w-full"
                    >
                      <option value="public">Publique</option>
                      <option value="unlisted">Non listée</option>
                      <option value="private">Privée</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Politique d'adhésion
                    </label>
                    <select
                      value={profileForm.membership_policy}
                      onChange={(e) => setProfileForm({...profileForm, membership_policy: e.target.value})}
                      className="input-primary w-full"
                    >
                      <option value="open">Ouverte</option>
                      <option value="request_only">Sur demande</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={profileForm.description}
                    onChange={(e) => setProfileForm({...profileForm, description: e.target.value})}
                    className="input-primary w-full"
                    rows="4"
                    placeholder="Décrivez votre organisation..."
                  />
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Site web
                    </label>
                    <input
                      type="url"
                      value={profileForm.website_url}
                      onChange={(e) => setProfileForm({...profileForm, website_url: e.target.value})}
                      className="input-primary w-full"
                      placeholder="https://example.com"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Discord
                    </label>
                    <input
                      type="url"
                      value={profileForm.discord_url}
                      onChange={(e) => setProfileForm({...profileForm, discord_url: e.target.value})}
                      className="input-primary w-full"
                      placeholder="https://discord.gg/..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Twitter
                    </label>
                    <input
                      type="url"
                      value={profileForm.twitter_url}
                      onChange={(e) => setProfileForm({...profileForm, twitter_url: e.target.value})}
                      className="input-primary w-full"
                      placeholder="https://twitter.com/..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      YouTube
                    </label>
                    <input
                      type="url"
                      value={profileForm.youtube_url}
                      onChange={(e) => setProfileForm({...profileForm, youtube_url: e.target.value})}
                      className="input-primary w-full"
                      placeholder="https://youtube.com/..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Twitch
                    </label>
                    <input
                      type="url"
                      value={profileForm.twitch_url}
                      onChange={(e) => setProfileForm({...profileForm, twitch_url: e.target.value})}
                      className="input-primary w-full"
                      placeholder="https://twitch.tv/..."
                    />
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <button type="submit" className="btn-primary">
                    Sauvegarder les modifications
                  </button>
                </div>
              </form>
            </div>
          )}

          {activeTab === 'media' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-6">Gestion des médias</h2>
              <div className="space-y-8">
                {/* Logo */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Logo de l'organisation</h3>
                  <div className="flex items-center space-x-6">
                    {organization.logo_url ? (
                      <img
                        src={organization.logo_url}
                        alt="Logo"
                        className="w-20 h-20 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-20 h-20 bg-dark-600 rounded-lg flex items-center justify-center">
                        <PhotoIcon className="w-8 h-8 text-gray-400" />
                      </div>
                    )}
                    <div>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleLogoUpload}
                        className="hidden"
                        id="logo-upload"
                      />
                      <label htmlFor="logo-upload" className="btn-secondary cursor-pointer">
                        {organization.logo_url ? 'Changer le logo' : 'Ajouter un logo'}
                      </label>
                      <p className="text-sm text-gray-400 mt-2">
                        Format recommandé: PNG, JPG (max 10MB)
                      </p>
                    </div>
                  </div>
                </div>

                {/* Banner */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Bannière de l'organisation</h3>
                  <div className="space-y-4">
                    {organization.banner_url ? (
                      <img
                        src={organization.banner_url}
                        alt="Bannière"
                        className="w-full h-48 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-full h-48 bg-dark-600 rounded-lg flex items-center justify-center">
                        <PhotoIcon className="w-12 h-12 text-gray-400" />
                      </div>
                    )}
                    <div>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleBannerUpload}
                        className="hidden"
                        id="banner-upload"
                      />
                      <label htmlFor="banner-upload" className="btn-secondary cursor-pointer">
                        {organization.banner_url ? 'Changer la bannière' : 'Ajouter une bannière'}
                      </label>
                      <p className="text-sm text-gray-400 mt-2">
                        Format recommandé: PNG, JPG, ratio 16:9 (max 10MB)
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'members' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-6">
                Gestion des membres ({members.length})
              </h2>
              <div className="space-y-4">
                {members.map((member) => {
                  const isOrgOwner = member.user_id === organization.owner_id;
                  return (
                    <div key={member.user_id} className="glass-effect rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
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
                          <div>
                            <h4 className="text-white font-semibold">{member.handle}</h4>
                            <p className="text-gray-400 text-sm">{member.discord_username}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-4">
                          {!isOrgOwner && isAdmin && (
                            <select
                              value={member.role}
                              onChange={(e) => handleMemberRoleChange(member.user_id, e.target.value)}
                              className="input-primary text-sm"
                            >
                              <option value="member">Membre</option>
                              <option value="moderator">Modérateur</option>
                              <option value="admin">Administrateur</option>
                            </select>
                          )}
                          
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            isOrgOwner
                              ? 'bg-purple-100 text-purple-800'
                              : member.role === 'admin'
                              ? 'bg-red-100 text-red-800'
                              : member.role === 'moderator'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {isOrgOwner ? 'Propriétaire' : 
                             member.role === 'admin' ? 'Admin' :
                             member.role === 'moderator' ? 'Modérateur' : 'Membre'}
                          </span>

                          {!isOrgOwner && isAdmin && (
                            <button
                              onClick={() => handleRemoveMember(member.user_id)}
                              className="text-red-400 hover:text-red-300 p-2"
                              title="Retirer le membre"
                            >
                              <XMarkIcon className="w-5 h-5" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === 'requests' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-6">
                Demandes d'adhésion ({joinRequests.length})
              </h2>
              {joinRequests.length > 0 ? (
                <div className="space-y-4">
                  {joinRequests.map((request) => (
                    <div key={request.id} className="glass-effect rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          {request.user_avatar_url ? (
                            <img
                              src={request.user_avatar_url}
                              alt={request.user_handle}
                              className="w-12 h-12 rounded-full mr-4"
                            />
                          ) : (
                            <div className="w-12 h-12 bg-dark-600 rounded-full flex items-center justify-center mr-4">
                              <span className="text-white font-bold">
                                {request.user_handle.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          )}
                          <div>
                            <h4 className="text-white font-semibold">{request.user_handle}</h4>
                            {request.message && (
                              <p className="text-gray-300 text-sm mt-1">{request.message}</p>
                            )}
                            <p className="text-gray-500 text-xs mt-1">
                              Demandé le {new Date(request.created_at).toLocaleDateString('fr-FR')}
                            </p>
                          </div>
                        </div>

                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleJoinRequestAction(request.id, 'accepted')}
                            className="btn-primary text-sm"
                          >
                            Accepter
                          </button>
                          <button
                            onClick={() => handleJoinRequestAction(request.id, 'rejected')}
                            className="btn-ghost text-red-400 hover:text-red-300 text-sm"
                          >
                            Refuser
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CheckCircleIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">Aucune demande d'adhésion en attente</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'danger' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-6">Zone de danger</h2>
              <div className="space-y-6">
                {/* Transfer Ownership */}
                <div className="border border-yellow-600 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-yellow-400 mb-2">
                    Transférer la propriété
                  </h3>
                  <p className="text-gray-300 mb-4">
                    Transférez définitivement la propriété de cette organisation à un autre membre.
                  </p>
                  <button
                    onClick={() => setShowTransferModal(true)}
                    className="btn-secondary text-yellow-400 border-yellow-400 hover:bg-yellow-400 hover:text-dark-900"
                  >
                    <ArrowRightOnRectangleIcon className="w-5 h-5 mr-2" />
                    Transférer la propriété
                  </button>
                </div>

                {/* Delete Organization */}
                <div className="border border-red-600 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-red-400 mb-2">
                    Supprimer l'organisation
                  </h3>
                  <p className="text-gray-300 mb-4">
                    Supprimez définitivement cette organisation. Cette action est irréversible.
                  </p>
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="btn-secondary text-red-400 border-red-400 hover:bg-red-400 hover:text-white"
                  >
                    <TrashIcon className="w-5 h-5 mr-2" />
                    Supprimer l'organisation
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Transfer Ownership Modal */}
        {showTransferModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-dark-800 rounded-lg p-6 max-w-md w-full">
              <h3 className="text-xl font-bold text-white mb-4">
                Transférer la propriété
              </h3>
              <p className="text-gray-300 mb-6">
                Sélectionnez le nouveau propriétaire de cette organisation. Cette action est irréversible.
              </p>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nouveau propriétaire
                </label>
                <select
                  value={selectedNewOwner}
                  onChange={(e) => setSelectedNewOwner(e.target.value)}
                  className="input-primary w-full"
                >
                  <option value="">Sélectionner un membre...</option>
                  {members
                    .filter(m => m.user_id !== user.id)
                    .map(member => (
                      <option key={member.user_id} value={member.user_id}>
                        {member.handle} ({member.role})
                      </option>
                    ))}
                </select>
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowTransferModal(false)}
                  className="btn-ghost flex-1"
                >
                  Annuler
                </button>
                <button
                  onClick={handleTransferOwnership}
                  disabled={!selectedNewOwner}
                  className="btn-primary flex-1 bg-yellow-600 hover:bg-yellow-700"
                >
                  Confirmer le transfert
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-dark-800 rounded-lg p-6 max-w-md w-full">
              <div className="flex items-center mb-4">
                <ExclamationTriangleIcon className="w-8 h-8 text-red-400 mr-3" />
                <h3 className="text-xl font-bold text-white">
                  Supprimer l'organisation
                </h3>
              </div>
              
              <p className="text-gray-300 mb-6">
                Êtes-vous absolument sûr de vouloir supprimer <strong>{organization.name}</strong> ?
                Cette action supprimera définitivement l'organisation, tous ses membres, événements et données associées.
                Cette action est <strong>irréversible</strong>.
              </p>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="btn-ghost flex-1"
                >
                  Annuler
                </button>
                <button
                  onClick={handleDeleteOrganization}
                  className="btn-primary flex-1 bg-red-600 hover:bg-red-700"
                >
                  Oui, supprimer définitivement
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ManageOrganizationPage;