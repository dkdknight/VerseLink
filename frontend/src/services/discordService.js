import { api } from './authService';

export const discordService = {
  // Guild Management
  registerGuild: async (guildData, orgId = null) => {
    try {
      const params = orgId ? { org_id: orgId } : {};
      const response = await api.post('/discord/guilds', guildData, { params });
      return response.data;
    } catch (error) {
      console.error('Failed to register Discord guild:', error);
      throw error;
    }
  },

  linkGuild: async (guildId, orgId) => {
    try {
      const response = await api.post(`/discord/guilds/${guildId}/link`, { org_id: orgId });
      return response.data;
    } catch (error) {
      console.error('Failed to link Discord guild:', error);
      throw error;
    }
  },

  getGuilds: async (orgId = null) => {
    try {
      const params = orgId ? { org_id: orgId } : {};
      const response = await api.get('/discord/guilds', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get Discord guilds:', error);
      throw error;
    }
  },

  getGuild: async (guildId) => {
    try {
      const response = await api.get(`/discord/guilds/${guildId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get Discord guild:', error);
      throw error;
    }
  },

  // Announcements
  announceEvent: async (announcement) => {
    try {
      const response = await api.post('/discord/announce/event', announcement);
      return response.data;
    } catch (error) {
      console.error('Failed to announce event:', error);
      throw error;
    }
  },

  announceTournament: async (announcement) => {
    try {
      const response = await api.post('/discord/announce/tournament', announcement);
      return response.data;
    } catch (error) {
      console.error('Failed to announce tournament:', error);
      throw error;
    }
  },

  // Message Synchronization
  syncMessage: async (syncRequest) => {
    try {
      const response = await api.post('/discord/sync/message', syncRequest);
      return response.data;
    } catch (error) {
      console.error('Failed to sync message:', error);
      throw error;
    }
  },

  // Reminders
  scheduleEventReminders: async (eventId) => {
    try {
      const response = await api.post(`/discord/reminders/schedule/${eventId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to schedule reminders:', error);
      throw error;
    }
  },

  // Job Management (Admin)
  getJobs: async (params = {}) => {
    try {
      const response = await api.get('/discord/jobs', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get Discord jobs:', error);
      throw error;
    }
  },

  processJobs: async () => {
    try {
      const response = await api.post('/discord/jobs/process');
      return response.data;
    } catch (error) {
      console.error('Failed to process Discord jobs:', error);
      throw error;
    }
  },

  // Statistics and Health
  getStats: async () => {
    try {
      const response = await api.get('/discord/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to get Discord stats:', error);
      throw error;
    }
  },

  getHealth: async () => {
    try {
      const response = await api.get('/discord/health');
      return response.data;
    } catch (error) {
      console.error('Failed to get Discord health:', error);
      throw error;
    }
  }
};