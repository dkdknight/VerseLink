import React, { useEffect, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useAuth } from '../App';
import { authService } from '../services/authService';

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [authUrl, setAuthUrl] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const { isAuthenticated, login } = useAuth();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Handle Discord OAuth callback
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      toast.error('Authentification annulée');
      return;
    }

    if (code) {
      handleDiscordCallback(code, state);
    } else {
      loadDiscordAuthUrl();
    }
  }, [searchParams]);

  const loadDiscordAuthUrl = async () => {
    try {
      const response = await authService.getDiscordAuthUrl();
      setAuthUrl(response.auth_url);
    } catch (error) {
      console.error('Failed to load Discord auth URL:', error);
      toast.error('Erreur lors du chargement de l\'authentification');
    }
  };

  const handleDiscordCallback = async (code, state) => {
    try {
      setLoading(true);
      const remember = localStorage.getItem('remember_me') === 'true';
      await login(code, state, remember);
      toast.success('Connexion réussie !');
    } catch (error) {
      console.error('Login failed:', error);
      const message = error.response?.data?.detail || 'Échec de la connexion. Veuillez réessayer.';
      toast.error(message);
    } finally {
      localStorage.removeItem('remember_me');
      setLoading(false);
    }
  };

  const handleDiscordLogin = () => {
    if (authUrl) {
      localStorage.setItem('remember_me', rememberMe ? 'true' : 'false');
      window.location.href = authUrl;
    } else {
      toast.error('URL d\'authentification non disponible');
    }
  };

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Show loading if processing OAuth callback
  if (loading || searchParams.get('code')) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner w-16 h-16 mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-white mb-2">Connexion en cours...</h2>
          <p className="text-gray-400">Vérification avec Discord</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-star rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">V</span>
            </div>
          </div>
          <h2 className="text-4xl font-bold text-white mb-2 text-shadow">
            Bienvenue sur VerseLink
          </h2>
          <p className="text-gray-400 text-lg">
            Connectez-vous avec Discord pour rejoindre la communauté Star Citizen
          </p>
        </div>

        {/* Login Card */}
        <div className="glass-effect rounded-2xl p-8 space-y-6">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-4">Connexion</h3>
            <p className="text-gray-400 mb-8">
              Utilisez votre compte Discord pour accéder à toutes les fonctionnalités de VerseLink.
            </p>
          </div>

          {/* Remember Me Option */}
          <div className="flex items-center justify-center mb-4">
            <input
              id="rememberMe"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-primary-500 focus:ring-primary-400 border-gray-600 rounded"
            />
            <label htmlFor="rememberMe" className="ml-2 block text-sm text-gray-300">
              Rester connecté
            </label>
          </div>

          {/* Discord Login Button */}
          <button
            onClick={handleDiscordLogin}
            disabled={!authUrl || loading}
            className="discord-button w-full flex items-center justify-center px-6 py-4 rounded-xl text-white font-semibold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed focus-ring"
          >
            <svg className="w-6 h-6 mr-3" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419-.0002 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1568 2.4189Z"/>
            </svg>
            Se connecter avec Discord
          </button>

          {/* Features List */}
          <div className="mt-8 space-y-4">
            <div className="text-center text-gray-400 text-sm mb-4">
              En vous connectant, vous pourrez :
            </div>
            <div className="grid gap-3">
              <div className="flex items-center text-gray-300">
                <div className="w-2 h-2 bg-primary-400 rounded-full mr-3"></div>
                <span className="text-sm">Rejoindre des organisations Star Citizen</span>
              </div>
              <div className="flex items-center text-gray-300">
                <div className="w-2 h-2 bg-primary-400 rounded-full mr-3"></div>
                <span className="text-sm">Participer à des événements et missions</span>
              </div>
              <div className="flex items-center text-gray-300">
                <div className="w-2 h-2 bg-primary-400 rounded-full mr-3"></div>
                <span className="text-sm">Créer et gérer vos propres tournois</span>
              </div>
              <div className="flex items-center text-gray-300">
                <div className="w-2 h-2 bg-primary-400 rounded-full mr-3"></div>
                <span className="text-sm">Synchroniser avec vos serveurs Discord</span>
              </div>
            </div>
          </div>
        </div>

        {/* Security Notice */}
        <div className="text-center text-sm text-gray-500">
          <p>
            Vos données Discord sont sécurisées et ne seront utilisées que pour 
            l'authentification et l'amélioration de votre expérience sur VerseLink.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;