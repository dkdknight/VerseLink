import { api } from './authService';

export const autoModerationService = {
  // Get auto-moderation configuration (admin only)
  getConfig: async () => {
    try {
      const response = await api.get('/auto-moderation/config');
      return response.data;
    } catch (error) {
      console.error('Failed to get auto-moderation config:', error);
      throw error;
    }
  },

  // Update auto-moderation configuration (admin only)
  updateConfig: async (config) => {
    try {
      const response = await api.put('/auto-moderation/config', config);
      return response.data;
    } catch (error) {
      console.error('Failed to update auto-moderation config:', error);
      throw error;
    }
  },

  // Toggle auto-moderation on/off (admin only)
  toggle: async (enabled) => {
    try {
      const response = await api.post(`/auto-moderation/toggle?enabled=${enabled}`);
      return response.data;
    } catch (error) {
      console.error('Failed to toggle auto-moderation:', error);
      throw error;
    }
  },

  // Check message content for violations (testing)
  checkMessage: async (content, context = null) => {
    try {
      const response = await api.post('/auto-moderation/check-message', {
        content,
        context
      });
      return response.data;
    } catch (error) {
      console.error('Failed to check message:', error);
      throw error;
    }
  },

  // Get auto-moderation statistics (admin only)
  getStats: async () => {
    try {
      const response = await api.get('/auto-moderation/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to get auto-moderation stats:', error);
      throw error;
    }
  },

  // Get auto-moderation logs (admin only)
  getLogs: async (params = {}) => {
    try {
      const response = await api.get('/auto-moderation/logs', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get auto-moderation logs:', error);
      throw error;
    }
  },

  // Clear old auto-moderation logs (admin only)
  clearOldLogs: async (daysOld = 30) => {
    try {
      const response = await api.delete(`/auto-moderation/logs?days_old=${daysOld}`);
      return response.data;
    } catch (error) {
      console.error('Failed to clear old logs:', error);
      throw error;
    }
  }
};