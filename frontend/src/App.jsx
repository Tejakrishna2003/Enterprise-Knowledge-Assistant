import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWorkspace from './components/ChatWorkspace';
import CitationInspectorModal from './components/CitationInspectorModal';
import DocumentLibraryModal from './components/DocumentLibraryModal';
import DocumentPreviewModal from './components/DocumentPreviewModal';
import { api } from './services/api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [demoUsers, setDemoUsers] = useState([]);
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [documents, setDocuments] = useState([]);
  
  // UI Modals & Drawers
  const [showDocLibrary, setShowDocLibrary] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [previewDocId, setPreviewDocId] = useState(null);

  // States
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [initError, setInitError] = useState(null);

  // Initial Load: User & Demo accounts
  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    try {
      setLoading(true);
      setInitError(null);
      const [user, users] = await Promise.all([
        api.getCurrentUser(),
        api.getDemoUsers()
      ]);
      setCurrentUser(user);
      setDemoUsers(users);
      await loadWorkspaces(user);
    } catch (err) {
      console.error(err);
      setInitError(err.message || 'Failed to connect to backend server. Ensure FastAPI is running on http://127.0.0.1:8000');
      setLoading(false);
    }
  };

  const loadWorkspaces = async (user) => {
    try {
      const wsList = await api.getWorkspaces();
      setWorkspaces(wsList);
      if (wsList.length > 0) {
        const defaultWs = wsList[0];
        setActiveWorkspace(defaultWs);
        await loadWorkspaceData(defaultWs._id);
      } else {
        setActiveWorkspace(null);
        setConversations([]);
        setActiveConversation(null);
        setDocuments([]);
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const loadWorkspaceData = async (workspaceId) => {
    try {
      const [docs, convs] = await Promise.all([
        api.getDocuments(workspaceId),
        api.getConversations(workspaceId)
      ]);
      setDocuments(docs);
      setConversations(convs);

      // Select first conversation if available, or reset to empty
      if (convs.length > 0) {
        const fullConv = await api.getConversation(workspaceId, convs[0]._id);
        setActiveConversation(fullConv);
      } else {
        setActiveConversation(null);
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  // Switch demo account
  const handleSwitchUser = async (userId) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.switchUser(userId);
      setCurrentUser(res.user);
      await loadWorkspaces(res.user);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Switch workspace
  const handleSelectWorkspace = async (ws) => {
    setActiveWorkspace(ws);
    setError(null);
    setLoading(true);
    await loadWorkspaceData(ws._id);
    setLoading(false);
  };

  // Switch conversation
  const handleSelectConversation = async (convId) => {
    if (!activeWorkspace) return;
    try {
      setError(null);
      const conv = await api.getConversation(activeWorkspace._id, convId);
      setActiveConversation(conv);
    } catch (err) {
      setError(err.message);
    }
  };

  // Start new conversation
  const handleNewConversation = async () => {
    if (!activeWorkspace) return;
    try {
      setError(null);
      const newConv = await api.createConversation(activeWorkspace._id, 'New Conversation');
      setConversations([newConv, ...conversations]);
      setActiveConversation(newConv);
    } catch (err) {
      setError(err.message);
    }
  };

  // Send message
  const handleSendMessage = async (content) => {
    if (!activeWorkspace) return;

    let targetConvId = activeConversation?._id;

    // If no active conversation, create one first
    if (!targetConvId) {
      try {
        const newConv = await api.createConversation(activeWorkspace._id, content.slice(0, 30));
        targetConvId = newConv._id;
        setActiveConversation(newConv);
        setConversations([newConv, ...conversations]);
      } catch (err) {
        setError(err.message);
        return;
      }
    }

    // Optimistically append user message to UI
    const tempUserMsg = {
      id: `temp_${Date.now()}`,
      sender: 'user',
      content,
      status: 'COMPLETED',
      citations: [],
      timestamp: new Date().toISOString()
    };

    setActiveConversation((prev) => ({
      ...prev,
      messages: [...(prev?.messages || []), tempUserMsg]
    }));

    setSending(true);
    setError(null);

    try {
      const asstMsg = await api.sendMessage(activeWorkspace._id, targetConvId, content);
      
      // Update active conversation with confirmed assistant message
      setActiveConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages || []).filter((m) => m.id !== tempUserMsg.id), tempUserMsg, asstMsg]
      }));

      // Refresh conversations list to update title and updated_at
      const updatedConvs = await api.getConversations(activeWorkspace._id);
      setConversations(updatedConvs);
      const matchingConv = updatedConvs.find((c) => c._id === targetConvId);
      if (matchingConv) {
        setActiveConversation((prev) => ({
          ...prev,
          title: matchingConv.title
        }));
      }
      setSending(false);
    } catch (err) {
      setSending(false);
      setError(err.message || 'Failed to generate response.');
      
      // If error occurs, reload full conversation to show actual saved failed state
      if (targetConvId) {
        api.getConversation(activeWorkspace._id, targetConvId)
          .then((conv) => setActiveConversation(conv))
          .catch(() => {});
      }
    }
  };

  if (initError) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-900 p-6">
        <div className="bg-slate-800 border border-slate-700 max-w-md w-full rounded-2xl p-8 shadow-2xl text-center">
          <div className="w-16 h-16 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 text-rose-400">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Backend Connection Failed</h2>
          <p className="text-sm text-slate-300 mb-6 leading-relaxed">
            {initError}
          </p>
          <div className="text-xs bg-slate-900/80 p-3 rounded-lg text-slate-400 font-mono mb-6 text-left">
            cd backend<br />
            .\venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000
          </div>
          <button
            onClick={initApp}
            className="w-full bg-sky-600 hover:bg-sky-500 text-white font-semibold py-2.5 px-4 rounded-xl transition cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-100">
      {/* Top Header */}
      <Header
        currentUser={currentUser}
        demoUsers={demoUsers}
        onSwitchUser={handleSwitchUser}
        activeWorkspace={activeWorkspace}
        loading={loading}
      />

      {/* Main Dual-Pane Body */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          workspaces={workspaces}
          activeWorkspace={activeWorkspace}
          onSelectWorkspace={handleSelectWorkspace}
          conversations={conversations}
          activeConversation={activeConversation}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onOpenDocLibrary={() => setShowDocLibrary(true)}
          documentCount={documents.length}
        />

        <ChatWorkspace
          conversation={activeConversation}
          messages={activeConversation?.messages || []}
          onSendMessage={handleSendMessage}
          onInspectCitation={(citation) => setSelectedCitation(citation)}
          activeWorkspace={activeWorkspace}
          sending={sending}
          error={error}
          onDismissError={() => setError(null)}
        />
      </div>

      {/* Modals & Inspectors */}
      {selectedCitation && (
        <CitationInspectorModal
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
          onOpenDocument={(docId) => {
            setSelectedCitation(null);
            setPreviewDocId(docId);
          }}
        />
      )}

      {showDocLibrary && activeWorkspace && (
        <DocumentLibraryModal
          workspace={activeWorkspace}
          documents={documents}
          onClose={() => setShowDocLibrary(false)}
          onRefreshDocs={() => api.getDocuments(activeWorkspace._id).then(setDocuments)}
          onSelectDocPreview={(docId) => setPreviewDocId(docId)}
        />
      )}

      {previewDocId && activeWorkspace && (
        <DocumentPreviewModal
          documentId={previewDocId}
          workspaceId={activeWorkspace._id}
          onClose={() => setPreviewDocId(null)}
        />
      )}
    </div>
  );
}
