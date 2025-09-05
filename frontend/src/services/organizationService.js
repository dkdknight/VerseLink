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
  }
};