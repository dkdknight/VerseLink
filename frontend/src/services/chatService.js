import { api } from './authService';

export const chatService = {
  getMessages: async (type, id) => {
    const response = await api.get(`/chat/${type}/${id}/messages`);
    return response.data;
  },
  postMessage: async (type, id, content) => {
    const response = await api.post(`/chat/${type}/${id}/messages`, { content });
    return response.data;
  },
  connectWebSocket: (type, id, token, onMessage) => {
    const base = (process.env.REACT_APP_BACKEND_WS_URL || 'ws://localhost:8001');
    const ws = new WebSocket(`${base}/api/v1/chat/ws/${type === 'events' ? 'event' : 'match'}/${id}?token=${token}`);
    ws.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data));
      } catch {}
    };
    return ws;
  }
};