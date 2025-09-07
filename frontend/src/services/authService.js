import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth service
export const authService = {
  // Set authentication token
  setAuthToken: (token) => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  },

  // Clear authentication token
  clearAuthToken: () => {
    delete api.defaults.headers.common['Authorization'];
  },

  // Get Discord OAuth redirect URL
  getDiscordAuthUrl: async () => {
    try {
      const response = await api.get('/auth/discord/redirect');
      return response.data;
    } catch (error) {
      console.error('Failed to get Discord auth URL:', error);
      throw error;
    }
  },

  // Handle Discord OAuth callback
  discordCallback: async (code, state) => {
    try {
      const response = await api.post('/auth/discord/callback', { code, state });
      return response.data;
    } catch (error) {
      console.error('Discord callback failed:', error);
      throw error;
    }
  },

  // Check authentication status
  checkAuth: async () => {
    try {
      const response = await api.get('/auth/check');
      return response.data;
    } catch (error) {
      console.error('Auth check failed:', error);
      throw error;
    }
  },

  // Get current user profile
  getCurrentUser: async () => {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get current user:', error);
      throw error;
    }
  },

  // Logout
  logout: async () => {
    try {
      const response = await api.post('/auth/logout');
      return response.data;
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }
};

// Export axios instance for other services
export { api };