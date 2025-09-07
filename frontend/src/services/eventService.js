import { api } from './authService';

export const eventService = {
  // List events with filters
  listEvents: async (params = {}) => {
    try {
      const response = await api.get('/events/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list events:', error);
      throw error;
    }
  },

  // Get event details
  getEvent: async (eventId) => {
    try {
      const response = await api.get(`/events/${eventId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get event:', error);
      throw error;
    }
  },

  // Create event for organization
  createEvent: async (orgId, eventData) => {
    try {
      const response = await api.post(`/orgs/${orgId}/events`, eventData);
      return response.data;
    } catch (error) {
      console.error('Failed to create event:', error);
      throw error;
    }
  },

  // Update event
  updateEvent: async (eventId, updateData) => {
    try {
      const response = await api.patch(`/events/${eventId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Failed to update event:', error);
      throw error;
    }
  },

  // Delete event
  deleteEvent: async (eventId) => {
    try {
      const response = await api.delete(`/events/${eventId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete event:', error);
      throw error;
    }
  },

  // Sign up for event
  signupForEvent: async (eventId, signupData) => {
    try {
      const response = await api.post(`/events/${eventId}/signups`, signupData);
      return response.data;
    } catch (error) {
      console.error('Failed to signup for event:', error);
      throw error;
    }
  },

  // Withdraw from event
  withdrawFromEvent: async (eventId) => {
    try {
      const response = await api.delete(`/events/${eventId}/signups/me`);
      return response.data;
    } catch (error) {
      console.error('Failed to withdraw from event:', error);
      throw error;
    }
  },

  // Check in for event
  checkinForEvent: async (eventId) => {
    try {
      const response = await api.post(`/events/${eventId}/checkin`);
      return response.data;
    } catch (error) {
      console.error('Failed to checkin for event:', error);
      throw error;
    }
  },

  // Download event iCal
  downloadEventICS: async (eventId) => {
    try {
      const response = await api.get(`/events/${eventId}/ics`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `event-${eventId}.ics`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Failed to download event ICS:', error);
      throw error;
    }
  }
};