const API_BASE = '/api';

let currentUserId = localStorage.getItem('demo_user_id') || 'usr_alice';

export const setStoredUser = (userId) => {
  currentUserId = userId;
  localStorage.setItem('demo_user_id', userId);
};

export const getStoredUser = () => currentUserId;

const getHeaders = (extra = {}) => ({
  'X-User-Id': currentUserId,
  ...extra
});

export const api = {
  // Auth
  getCurrentUser: async () => {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch user');
    return res.json();
  },

  getDemoUsers: async () => {
    const res = await fetch(`${API_BASE}/auth/users`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch demo users');
    return res.json();
  },

  switchUser: async (userId) => {
    const res = await fetch(`${API_BASE}/auth/switch-user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    if (!res.ok) throw new Error('Failed to switch user');
    const data = await res.json();
    setStoredUser(userId);
    return data;
  },

  // Workspaces
  getWorkspaces: async () => {
    const res = await fetch(`${API_BASE}/workspaces`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch workspaces');
    return res.json();
  },

  getWorkspace: async (workspaceId) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}`, { headers: getHeaders() });
    if (!res.ok) {
      if (res.status === 403) throw new Error('Access to this workspace is forbidden.');
      throw new Error('Failed to fetch workspace');
    }
    return res.json();
  },

  // Documents
  getDocuments: async (workspaceId) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents`, { headers: getHeaders() });
    if (!res.ok) {
      if (res.status === 403) throw new Error('Access forbidden.');
      throw new Error('Failed to fetch documents');
    }
    return res.json();
  },

  getDocumentDetail: async (workspaceId, documentId) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents/${documentId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch document details');
    return res.json();
  },

  uploadDocument: async (workspaceId, file, title) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);

    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents`, {
      method: 'POST',
      headers: getHeaders(),
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to upload document');
    }
    return res.json();
  },

  // Conversations & Chat
  getConversations: async (workspaceId) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },

  createConversation: async (workspaceId, title = 'New Conversation') => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title })
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },

  getConversation: async (workspaceId, conversationId) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations/${conversationId}`, { headers: getHeaders() });
    if (!res.ok) {
      if (res.status === 404 || res.status === 403) throw new Error('Conversation not found or access denied.');
      throw new Error('Failed to load conversation');
    }
    return res.json();
  },

  sendMessage: async (workspaceId, conversationId, content) => {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ content })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to send message');
    }
    return res.json();
  }
};
