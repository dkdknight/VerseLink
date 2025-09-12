/**
 * Authentication utilities
 */

export const ensureAuthenticated = () => {
  const token = localStorage.getItem('auth_token');
  if (!token || token.trim() === '') {
    throw new Error('No authentication token found. Please log in.');
  }
  return token;
};

export const isTokenExpired = (token) => {
  if (!token) return true;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch (error) {
    console.error('Error checking token expiration:', error);
    return true;
  }
};

export const handleAuthError = (error) => {
  if (error.response && error.response.status === 401) {
    // Clear invalid token
    localStorage.removeItem('auth_token');
    
    // Redirect to login if we're not already there
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    
    throw new Error('Session expired. Please log in again.');
  }
  throw error;
};