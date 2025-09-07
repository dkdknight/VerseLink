import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './App.css';

// Import components
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import OrganizationsPage from './pages/OrganizationsPage';
import OrganizationDetailPage from './pages/OrganizationDetailPage';
import CreateOrganizationPage from './pages/CreateOrganizationPage';
import EventsPage from './pages/EventsPage';
import EventDetailPage from './pages/EventDetailPage';
import TournamentsPage from './pages/TournamentsPage';
import TournamentDetailPage from './pages/TournamentDetailPage';
import NotificationsPage from './pages/NotificationsPage';
import NotificationPreferencesPage from './pages/NotificationPreferencesPage';
import ModerationDashboardPage from './pages/ModerationDashboardPage';
import DiscordIntegrationPage from './pages/DiscordIntegrationPage';
import DiscordCallbackPage from './pages/DiscordCallbackPage';
import AdminSetupPage from './pages/AdminSetupPage';

// Import services
import { authService } from './services/authService';
import { userService } from './services/userService';

// Auth Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      
      if (token) {
        // Set token in axios defaults
        authService.setAuthToken(token);
        
        // Verify token and get user
        const userData = await authService.checkAuth();
        setUser(userData.user);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // Clear invalid token
      localStorage.removeItem('auth_token');
      authService.clearAuthToken();
    } finally {
      setLoading(false);
    }
  };

  const login = async (code, state) => {
    try {
      const response = await authService.discordCallback(code, state);
      
      // Store token
      localStorage.setItem('auth_token', response.access_token);
      authService.setAuthToken(response.access_token);
      
      // Set user state
      setUser(response.user);
      setIsAuthenticated(true);
      
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Call backend logout endpoint
      await authService.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with client-side logout even if API fails
    } finally {
      // Always clear client-side auth state
      localStorage.removeItem('auth_token');
      authService.clearAuthToken();
      setUser(null);
      setIsAuthenticated(false);
      
      // Optional: redirect to home page
      navigate('/');
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const updatedUser = await userService.updateProfile(profileData);
      setUser(updatedUser);
      return updatedUser;
    } catch (error) {
      console.error('Profile update failed:', error);
      throw error;
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    updateProfile,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// Main App Component
function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="min-h-screen bg-dark-950">
          {/* Background stars effect */}
          <div className="star-field fixed inset-0 pointer-events-none"></div>
          
          <Navbar />
          
          <main className="relative z-10">
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/auth/discord/callback" element={<DiscordCallbackPage />} />
              <Route path="/organizations" element={<OrganizationsPage />} />
              <Route path="/organizations/create" element={<ProtectedRoute><CreateOrganizationPage /></ProtectedRoute>} />
              <Route path="/organizations/:id" element={<OrganizationDetailPage />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/events/:id" element={<EventDetailPage />} />
              <Route path="/tournaments" element={<TournamentsPage />} />
              <Route path="/tournaments/:id" element={<TournamentDetailPage />} />
              
              {/* Protected routes */}
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/notifications" 
                element={
                  <ProtectedRoute>
                    <NotificationsPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/notifications/preferences" 
                element={
                  <ProtectedRoute>
                    <NotificationPreferencesPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/setup" 
                element={
                  <ProtectedRoute>
                    <AdminSetupPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/moderation" 
                element={
                  <ProtectedRoute>
                    <ModerationDashboardPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/discord" 
                element={
                  <ProtectedRoute>
                    <DiscordIntegrationPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* Catch all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1e293b',
                color: '#f1f5f9',
                border: '1px solid #475569'
              },
              success: {
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#f1f5f9'
                }
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#f1f5f9'
                }
              }
            }}
          />
        </div>
      </AuthProvider>
    </Router>
  );
}

export { AuthProvider };
export default App;