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

  // Get detailed team information
  getTeamDetails: async (tournamentId, teamId) => {
    try {
      const response = await api.get(`/tournaments/${tournamentId}/teams/${teamId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get team details:', error);
      throw error;
    }
  },

  // Update team information (captain only)
  updateTeam: async (tournamentId, teamId, teamData) => {
    try {
      const response = await api.put(`/tournaments/${tournamentId}/teams/${teamId}`, teamData);
      return response.data;
    } catch (error) {
      console.error('Failed to update team:', error);
      throw error;
    }
  },

  // Delete team (captain only)
  deleteTeam: async (tournamentId, teamId) => {
    try {
      const response = await api.delete(`/tournaments/${tournamentId}/teams/${teamId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete team:', error);
      throw error;
    }
  },

  // Leave team (non-captain members)
  leaveTeam: async (tournamentId, teamId) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/teams/${teamId}/leave`);
      return response.data;
    } catch (error) {
      console.error('Failed to leave team:', error);
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

  // Tournament Administration
  startTournament: async (tournamentId) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/start`);
      return response.data;
    } catch (error) {
      console.error('Failed to start tournament:', error);
      throw error;
    }
  },

  // Close tournament registration
  closeTournamentRegistration: async (tournamentId) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/close-registration`);
      return response.data;
    } catch (error) {
      console.error('Failed to close tournament registration:', error);
      throw error;
    }
  },

  // Reopen tournament registration
  reopenTournamentRegistration: async (tournamentId) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/reopen-registration`);
      return response.data;
    } catch (error) {
      console.error('Failed to reopen tournament registration:', error);
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

  // Schedule a match
  scheduleMatch: async (matchId, scheduledAt) => {
    try {
      const response = await api.post(`/tournaments/matches/${matchId}/schedule`, {
        scheduled_at: scheduledAt,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to schedule match:', error);
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
  },

  // Team Invitations
  createTeamInvitation: async (tournamentId, teamId, invitationData) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/teams/${teamId}/invitations`, invitationData);
      return response.data;
    } catch (error) {
      console.error('Failed to create team invitation:', error);
      throw error;
    }
  },

  getTeamInvitations: async (tournamentId, teamId) => {
    try {
      const response = await api.get(`/tournaments/${tournamentId}/teams/${teamId}/invitations`);
      return response.data;
    } catch (error) {
      console.error('Failed to get team invitations:', error);
      throw error;
    }
  },

  respondToInvitation: async (invitationId, accept) => {
    try {
      const formData = new FormData();
      formData.append('accept', accept);
      
      const response = await api.post(`/tournaments/invitations/${invitationId}/respond`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to respond to invitation:', error);
      throw error;
    }
  },

  cancelInvitation: async (invitationId) => {
    try {
      const response = await api.delete(`/tournaments/invitations/${invitationId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to cancel invitation:', error);
      throw error;
    }
  },

  getMyInvitations: async (status = null) => {
    try {
      const params = {};
      if (status) params.status = status;
      
      const response = await api.get('/tournaments/invitations/me', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get my invitations:', error);
      throw error;
    }
  },

  // Match Disputes
  createMatchDispute: async (matchId, disputeData) => {
    try {
      const response = await api.post(`/tournaments/matches/${matchId}/dispute`, disputeData);
      return response.data;
    } catch (error) {
      console.error('Failed to create match dispute:', error);
      throw error;
    }
  },

  getMatchDisputes: async (matchId) => {
    try {
      const response = await api.get(`/tournaments/matches/${matchId}/disputes`);
      return response.data;
    } catch (error) {
      console.error('Failed to get match disputes:', error);
      throw error;
    }
  },

  listDisputes: async (params = {}) => {
    try {
      const response = await api.get('/tournaments/disputes', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list disputes:', error);
      throw error;
    }
  },

  getDispute: async (disputeId) => {
    try {
      const response = await api.get(`/tournaments/disputes/${disputeId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get dispute:', error);
      throw error;
    }
  },

  setDisputeUnderReview: async (disputeId) => {
    try {
      const response = await api.post(`/tournaments/disputes/${disputeId}/review`);
      return response.data;
    } catch (error) {
      console.error('Failed to set dispute under review:', error);
      throw error;
    }
  },

  resolveDispute: async (disputeId, approve, adminResponse) => {
    try {
      const formData = new FormData();
      formData.append('approve', approve);
      formData.append('admin_response', adminResponse);
      
      const response = await api.post(`/tournaments/disputes/${disputeId}/resolve`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to resolve dispute:', error);
      throw error;
    }
  },

  // Player Search
  createPlayerSearch: async (tournamentId, searchData) => {
    try {
      const response = await api.post(`/tournaments/${tournamentId}/player-search`, searchData);
      return response.data;
    } catch (error) {
      console.error('Failed to create player search:', error);
      throw error;
    }
  },

  getPlayerSearches: async (tournamentId, filters = {}) => {
    try {
      const params = {};
      if (filters.role) params.role = filters.role;
      if (filters.experience) params.experience = filters.experience;
      
      const response = await api.get(`/tournaments/${tournamentId}/player-search`, { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get player searches:', error);
      throw error;
    }
  },

  getMyPlayerSearches: async () => {
    try {
      const response = await api.get('/tournaments/player-search/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get my player searches:', error);
      throw error;
    }
  },

  updatePlayerSearch: async (searchId, searchData) => {
    try {
      const response = await api.put(`/tournaments/player-search/${searchId}`, searchData);
      return response.data;
    } catch (error) {
      console.error('Failed to update player search:', error);
      throw error;
    }
  },

  deactivatePlayerSearch: async (searchId) => {
    try {
      const response = await api.post(`/tournaments/player-search/${searchId}/deactivate`);
      return response.data;
    } catch (error) {
      console.error('Failed to deactivate player search:', error);
      throw error;
    }
  },

  deletePlayerSearch: async (searchId) => {
    try {
      const response = await api.delete(`/tournaments/player-search/${searchId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete player search:', error);
      throw error;
    }
  }
};