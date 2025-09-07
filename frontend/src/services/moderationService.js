import { api } from './authService';

export const moderationService = {
  // Report user
  createReport: async (reportData) => {
    try {
      const response = await api.post('/moderation/reports', reportData);
      return response.data;
    } catch (error) {
      console.error('Failed to create report:', error);
      throw error;
    }
  },

  // Get reports (admin only)
  getReports: async (params = {}) => {
    try {
      const response = await api.get('/moderation/reports', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get reports:', error);
      throw error;
    }
  },

  // Get specific report (admin only)
  getReport: async (reportId) => {
    try {
      const response = await api.get(`/moderation/reports/${reportId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get report:', error);
      throw error;
    }
  },

  // Handle report (admin only)
  handleReport: async (reportId, actionData) => {
    try {
      const response = await api.post(`/moderation/reports/${reportId}/action`, actionData);
      return response.data;
    } catch (error) {
      console.error('Failed to handle report:', error);
      throw error;
    }
  },

  // Get user moderation history (admin only)
  getUserModerationHistory: async (userId) => {
    try {
      const response = await api.get(`/moderation/users/${userId}/history`);
      return response.data;
    } catch (error) {
      console.error('Failed to get user moderation history:', error);
      throw error;
    }
  },

  // Get moderation statistics (admin only)
  getModerationStats: async () => {
    try {
      const response = await api.get('/moderation/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to get moderation stats:', error);
      throw error;
    }
  },

  // Get audit logs (admin only)
  getAuditLogs: async (params = {}) => {
    try {
      const response = await api.get('/moderation/audit-logs', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get audit logs:', error);
      throw error;
    }
  },

  // Unban expired users (admin only)
  unbanExpiredUsers: async () => {
    try {
      const response = await api.post('/moderation/maintenance/unban-expired');
      return response.data;
    } catch (error) {
      console.error('Failed to unban expired users:', error);
      throw error;
    }
  }
};