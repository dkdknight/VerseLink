import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useAuth } from '../App';

const DiscordCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      if (error) {
        console.error('Discord OAuth error:', error, errorDescription);
        toast.error(`Erreur d'authentification: ${errorDescription || error}`);
        navigate('/login');
        return;
      }

      if (!code) {
        toast.error('Code d\'autorisation manquant');
        navigate('/login');
        return;
      }

      try {
        console.log('Processing Discord OAuth callback with code:', code);
        const remember = localStorage.getItem('remember_me') === 'true';
        await login(code, state, remember);
        toast.success('Connexion réussie !');
        navigate('/');
      } catch (error) {
        console.error('Login failed:', error);
        const message = error.response?.data?.detail || 'Échec de la connexion. Veuillez réessayer.';
        toast.error(message);
        navigate('/login');
      } finally {
        localStorage.removeItem('remember_me');
      }
    };

    handleCallback();
  }, [searchParams, login, navigate]);

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center">
      <div className="text-center">
        <div className="loading-spinner w-16 h-16 mx-auto mb-6"></div>
        <h2 className="text-2xl font-bold text-white mb-2">Connexion en cours...</h2>
        <p className="text-gray-400">Vérification avec Discord</p>
      </div>
    </div>
  );
};

export default DiscordCallbackPage;