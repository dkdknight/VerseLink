import { api } from './authService';

export const tournamentService = {
  // List tournaments with filters
  listTournaments: async (params = {}) => {
    try {
      const response = await api.get('/tournaments/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list tournaments:', error);
      throw error;
    }
  },

  // Get tournament details
  getTournament: async (tournamentId) => {
    try {
      const response = await api.get(`/tournaments/${tournamentId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get tournament:', error);
      throw error;
    }
  },

  // Create tournament for organization
  createTournament: async (orgId, tournamentData) => {
    try {
      const response = await api.post(`/orgs/${orgId}/tournaments`, tournamentData);
      return response.data;
    } catch (error) {
      console.error('Failed to create tournament:', error);
      throw error;
    }
  },

  // Create team for tournament
  createTeam: async (tournamentId, teamData) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/teams`, teamData);
      return response.data;
    } catch (error) {
      console.error('Failed to create team:', error);
      throw error;
    }
  },

  // Add member to team
  addTeamMember: async (tournamentId, teamId, userId) => {
    try {
      const formData = new FormData();
      formData.append('user_id', userId);
      
      const response = await api.post(`/tournaments/${tournamentId}/teams/${teamId}/members`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to add team member:', error);
      throw error;
    }
  },

  // Remove member from team
  removeTeamMember: async (tournamentId, teamId, userId) => {
    try {
      const response = await api.delete(`/tournaments/${tournamentId}/teams/${teamId}/members/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to remove team member:', error);
      throw error;
    }
  },

  // Report match score
  reportMatchScore: async (matchId, scoreData) => {
    try {
      const response = await api.post(`/tournaments/matches/${matchId}/report`, scoreData);
      return response.data;
    } catch (error) {
      console.error('Failed to report match score:', error);
      throw error;
    }
  },

  // Verify match result (referee only)
  verifyMatchResult: async (matchId) => {
    try {
      const response = await api.post(`/tournaments/matches/${matchId}/verify`);
      return response.data;
    } catch (error) {
      console.error('Failed to verify match result:', error);
      throw error;
    }
  },

  // Upload match attachment
  uploadMatchAttachment: async (matchId, file, description = '') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (description) {
        formData.append('description', description);
      }
      
      const response = await api.post(`/tournaments/matches/${matchId}/attachments`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to upload match attachment:', error);
      throw error;
    }
  },

  // Delete attachment
  deleteAttachment: async (attachmentId) => {
    try {
      const response = await api.delete(`/tournaments/attachments/${attachmentId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete attachment:', error);
      throw error;
    }
  },

  // Download attachment
  downloadAttachment: (attachmentId) => {
    // Return the download URL
    return `${api.defaults.baseURL}/tournaments/attachments/${attachmentId}/download`;
  }
};