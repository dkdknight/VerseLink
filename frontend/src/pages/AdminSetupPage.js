import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../App';
import { api } from '../services/authService';

const AdminSetupPage = () => {
  const [loading, setLoading] = useState(false);
  const [discordId, setDiscordId] = useState('');
  const [showTestAdmin, setShowTestAdmin] = useState(false);
  const { user, isAuthenticated, setUser, setIsAuthenticated } = useAuth();

  const createTestAdmin = async () => {
    setLoading(true);
    try {
      const response = await api.post('/auth/create-test-admin');
      
      // Store the token
      localStorage.setItem('auth_token', response.data.access_token);
      
      // Update auth context
      setUser(response.data.user);
      setIsAuthenticated(true);
      
      toast.success(response.data.message);
      
      // Refresh the page to show admin interface
      setTimeout(() => {
        window.location.reload();
      }, 2000);
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur lors de la création du test admin';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };
    setLoading(true);
    try {
      const response = await api.post('/auth/init-admin');
      toast.success(response.data.message);
      
      // Reload the page to refresh user permissions
      setTimeout(() => {
        window.location.reload();
      }, 2000);
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur lors de l\'initialisation';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const promoteUser = async (e) => {
    e.preventDefault();
    if (!discordId.trim()) {
      toast.error('Veuillez entrer un Discord ID');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post(`/auth/promote-admin?target_discord_id=${discordId.trim()}`);
      toast.success(response.data.message);
      setDiscordId('');
    } catch (error) {
      const message = error.response?.data?.detail || 'Erreur lors de la promotion';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="bg-dark-800 rounded-lg p-8 border border-dark-700 max-w-md w-full">
          <h1 className="text-2xl font-bold text-white mb-4">Administration</h1>
          <p className="text-gray-400 mb-6">
            Vous devez être connecté pour accéder à cette page.
          </p>
          <button
            onClick={() => window.location.href = '/login'}
            className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Se connecter
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-dark-800 rounded-lg p-8 border border-dark-700">
          <h1 className="text-3xl font-bold text-white mb-8">🛡️ Administration VerseLink</h1>
          
          {/* Current User Info */}
          <div className="bg-dark-700 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Utilisateur Actuel</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-gray-400">Nom:</span>
                <p className="text-white font-medium">{user?.handle || user?.discord_username || 'Non défini'}</p>
              </div>
              <div>
                <span className="text-gray-400">Discord ID:</span>
                <p className="text-white font-mono text-sm">{user?.discord_id || 'Non défini'}</p>
              </div>
              <div>
                <span className="text-gray-400">Statut Admin:</span>
                <p className={`font-medium ${user?.is_site_admin ? 'text-green-400' : 'text-red-400'}`}>
                  {user?.is_site_admin ? '✅ Administrateur' : '❌ Utilisateur Standard'}
                </p>
              </div>
              <div>
                <span className="text-gray-400">Email:</span>
                <p className="text-white">{user?.email || 'Non défini'}</p>
              </div>
            </div>
          </div>

          {/* Initialize First Admin */}
          {!user?.is_site_admin && (
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-6 mb-8">
              <h2 className="text-xl font-semibold text-yellow-300 mb-4">🚀 Initialisation Première Admin</h2>
              <p className="text-yellow-200 mb-4">
                Si vous êtes le premier utilisateur du système, vous pouvez vous auto-promouvoir administrateur.
                Cette action ne fonctionne que s'il n'y a aucun administrateur existant.
              </p>
              <button
                onClick={initializeFirstAdmin}
                disabled={loading}
                className="bg-yellow-600 text-white py-2 px-6 rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Initialisation...' : 'Devenir Premier Admin'}
              </button>
            </div>
          )}

          {/* Admin Functions */}
          {user?.is_site_admin && (
            <div className="space-y-8">
              {/* Promote User */}
              <div className="bg-dark-700 rounded-lg p-6">
                <h2 className="text-xl font-semibold text-white mb-4">👑 Promouvoir un Utilisateur</h2>
                <p className="text-gray-400 mb-4">
                  Promouvoir un utilisateur existant au rang d'administrateur.
                </p>
                
                <form onSubmit={promoteUser} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Discord ID de l'utilisateur
                    </label>
                    <input
                      type="text"
                      value={discordId}
                      onChange={(e) => setDiscordId(e.target.value)}
                      placeholder="123456789012345678"
                      className="w-full px-3 py-2 bg-dark-600 border border-dark-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Pour obtenir le Discord ID : Paramètres Discord → Avancé → Mode Développeur → Clic droit sur utilisateur → Copier l'ID
                    </p>
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-primary-600 text-white py-2 px-6 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Promotion...' : 'Promouvoir Admin'}
                  </button>
                </form>
              </div>

              {/* Admin Tools */}
              <div className="bg-dark-700 rounded-lg p-6">
                <h2 className="text-xl font-semibold text-white mb-4">🔧 Outils Admin</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <button
                    onClick={() => window.location.href = '/admin/moderation'}
                    className="bg-orange-600 text-white py-3 px-4 rounded-lg hover:bg-orange-700 transition-colors text-center"
                  >
                    🛡️ Modération
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/discord'}
                    className="bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors text-center"
                  >
                    💬 Discord
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/notifications/preferences'}
                    className="bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors text-center"
                  >
                    🔔 Notifications
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6 mt-8">
            <h2 className="text-xl font-semibold text-blue-300 mb-4">📖 Instructions</h2>
            <div className="space-y-2 text-blue-200">
              <p><strong>1. Premier Admin :</strong> Utilisez "Devenir Premier Admin" si vous êtes le premier utilisateur.</p>
              <p><strong>2. Promouvoir :</strong> Les admins peuvent promouvoir d'autres utilisateurs via leur Discord ID.</p>
              <p><strong>3. Discord ID :</strong> Activez le mode développeur Discord pour copier les IDs utilisateur.</p>
              <p><strong>4. Sécurité :</strong> Seuls les admins existants peuvent créer de nouveaux admins.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSetupPage;