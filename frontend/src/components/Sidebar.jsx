import React from 'react';
import {
  MessageSquare,
  Plus,
  BookOpen,
  FolderLock,
  ChevronDown,
  Layers,
  Clock
} from 'lucide-react';

export default function Sidebar({
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  conversations,
  activeConversation,
  onSelectConversation,
  onNewConversation,
  onOpenDocLibrary,
  documentCount = 0
}) {
  return (
    <aside className="w-72 bg-slate-900 text-slate-300 flex flex-col h-full border-r border-slate-800">
      {/* Workspace Selector */}
      <div className="p-4 border-b border-slate-800">
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1.5 flex items-center gap-1.5">
          <Layers size={13} className="text-sky-400" />
          <span>Workspace Scope</span>
        </label>
        <div className="relative">
          <select
            value={activeWorkspace?._id || ''}
            onChange={(e) => {
              const selected = workspaces.find((w) => w._id === e.target.value);
              if (selected) onSelectWorkspace(selected);
            }}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-hidden appearance-none pr-8 cursor-pointer"
          >
            {workspaces.map((w) => (
              <option key={w._id} value={w._id}>
                {w.name}
              </option>
            ))}
          </select>
          <ChevronDown
            size={14}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
          />
        </div>
      </div>

      {/* Action Buttons: New Chat & Document Library */}
      <div className="p-3 space-y-2 border-b border-slate-800">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold py-2 px-3 rounded-lg transition-colors shadow-sm cursor-pointer"
        >
          <Plus size={15} />
          <span>New Chat</span>
        </button>

        <button
          onClick={onOpenDocLibrary}
          className="w-full flex items-center justify-between bg-slate-800/80 hover:bg-slate-800 text-slate-200 text-xs font-medium py-2 px-3 rounded-lg border border-slate-700/60 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <BookOpen size={14} className="text-sky-400" />
            <span>Document Library</span>
          </div>
          <span className="bg-slate-700 text-sky-300 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
            {documentCount}
          </span>
        </button>
      </div>

      {/* Saved Conversations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-2 py-1 flex items-center gap-1.5">
          <Clock size={12} />
          <span>Chat History</span>
        </div>

        {conversations.length === 0 ? (
          <div className="text-center py-8 px-4 text-xs text-slate-500">
            No saved chats in this workspace. Start one above!
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = activeConversation?._id === conv._id;
            return (
              <button
                key={conv._id}
                onClick={() => onSelectConversation(conv._id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-2.5 group cursor-pointer ${
                  isActive
                    ? 'bg-sky-950/70 text-sky-200 border border-sky-800/60'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <MessageSquare
                  size={14}
                  className={`shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-500 group-hover:text-slate-300'}`}
                />
                <span className="truncate flex-1">{conv.title || 'Untitled Conversation'}</span>
              </button>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Persistent Storage</span>
        <span className="flex items-center gap-1 text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> MongoDB
        </span>
      </div>
    </aside>
  );
}
