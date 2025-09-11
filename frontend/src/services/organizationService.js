import { api } from './authService';

export const organizationService = {
  // Create organization
  createOrganization: async (orgData) => {
    try {
      const response = await api.post('/orgs/', orgData);
      return response.data;
    } catch (error) {
      console.error('Failed to create organization:', error);
      throw error;
    }
  },

  // List organizations
  listOrganizations: async (query = '', visibility = null, limit = 20, skip = 0) => {
    try {
      const params = { limit, skip };
      if (query) params.query = query;
      if (visibility) params.visibility = visibility;
      
      const response = await api.get('/orgs/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list organizations:', error);
      throw error;
    }
  },

  // Get organization by ID
  getOrganization: async (orgId) => {
    try {
      const response = await api.get(`/orgs/${orgId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get organization:', error);
      throw error;
    }
  },

  // Update organization
  updateOrganization: async (orgId, updateData) => {
    try {
      const response = await api.patch(`/orgs/${orgId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Failed to update organization:', error);
      throw error;
    }
  },

  // Get organization members
  getMembers: async (orgId) => {
    try {
      const response = await api.get(`/orgs/${orgId}/members`);
      return response.data;
    } catch (error) {
      console.error('Failed to get organization members:', error);
      throw error;
    }
  },

  // Join organization
  joinOrganization: async (orgId) => {
    try {
      const response = await api.post(`/orgs/${orgId}/members`);
      return response.data;
    } catch (error) {
      console.error('Failed to join organization:', error);
      throw error;
    }
  },

  // Leave organization
  leaveOrganization: async (orgId, userId) => {
    try {
      const response = await api.delete(`/orgs/${orgId}/members/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to leave organization:', error);
      throw error;
    }
  },

  // Update member role
  updateMemberRole: async (orgId, userId, role) => {
    try {
      const response = await api.patch(`/orgs/${orgId}/members/${userId}/role`, { role });
      return response.data;
    } catch (error) {
      console.error('Failed to update member role:', error);
      throw error;
    }
  },

  // Remove member
  removeMember: async (orgId, userId) => {
    try {
      const response = await api.delete(`/orgs/${orgId}/members/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to remove member:', error);
      throw error;
    }
  },

  // Join request methods
  createJoinRequest: async (orgId, message = '') => {
    try {
      const response = await api.post(`/orgs/${orgId}/join-requests`, { message });
      return response.data;
    } catch (error) {
      console.error('Failed to create join request:', error);
      throw error;
    }
  },

  getJoinRequests: async (orgId) => {
    try {
      const response = await api.get(`/orgs/${orgId}/join-requests`);
      return response.data;
    } catch (error) {
      console.error('Failed to get join requests:', error);
      throw error;
    }
  },

  processJoinRequest: async (orgId, requestId, status) => {
    try {
      const response = await api.patch(`/orgs/${orgId}/join-requests/${requestId}`, { status });
      return response.data;
    } catch (error) {
      console.error('Failed to process join request:', error);
      throw error;
    }
  },

  // Media upload methods
  uploadLogo: async (orgId, file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post(`/orgs/${orgId}/media/logo`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to upload logo:', error);
      throw error;
    }
  },

  uploadBanner: async (orgId, file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post(`/orgs/${orgId}/media/banner`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to upload banner:', error);
      throw error;
    }
  },

  // Ownership and deletion
  transferOwnership: async (orgId, newOwnerId) => {
    try {
      const response = await api.post(`/orgs/${orgId}/transfer-ownership`, {
        new_owner_id: newOwnerId,
        confirmation: true
      });
      return response.data;
    } catch (error) {
      console.error('Failed to transfer ownership:', error);
      throw error;
    }
  },

  deleteOrganization: async (orgId) => {
    try {
      const response = await api.delete(`/orgs/${orgId}?confirmation=true`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete organization:', error);
      throw error;
    }
  }
};