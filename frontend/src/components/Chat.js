import React, { useState, useEffect, useRef } from 'react';
import { chatService } from '../services/chatService';
import { useAuth } from '../App';
import { toast } from 'react-hot-toast';

const Chat = ({ contextType, contextId }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const wsRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    let ws;
    async function init() {
      try {
        const msgs = await chatService.getMessages(contextType, contextId);
        setMessages(msgs);
        ws = chatService.connectWebSocket(contextType, contextId, token, (msg) => {
          setMessages((prev) => [...prev, msg]);
          if (msg.sender_id !== user?.id) {
            toast(`Nouveau message de ${msg.sender_handle}`);
          }
        });
        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to load chat', err);
      }
    }
    init();
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, [contextType, contextId, user]);

  const send = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    try {
      await chatService.postMessage(contextType, contextId, input.trim());
      setInput('');
    } catch (err) {
      toast.error('Envoi échoué');
    }
  };

  return (
    <div className="border rounded p-4">
      <div className="h-64 overflow-y-auto mb-4">
        {messages.map(m => (
          <div key={m.id} className="mb-1">
            <strong>{m.sender_handle}</strong>: {m.content}
          </div>
        ))}
      </div>
      <form onSubmit={send} className="flex gap-2">
        <input className="flex-1 border p-1" value={input} onChange={e => setInput(e.target.value)} />
        <button type="submit" className="bg-blue-500 text-white px-3">Envoyer</button>
      </form>
    </div>
  );
};

export default Chat;