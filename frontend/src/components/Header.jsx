import React from 'react';
import { Shield, User, RefreshCw, Briefcase } from 'lucide-react';

export default function Header({
  currentUser,
  demoUsers,
  onSwitchUser,
  activeWorkspace,
  loading
}) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-xs z-10">
      {/* Brand & Workspace Name */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-sm">
          4S
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-semibold text-slate-900 text-base">Enterprise Knowledge Assistant</h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-medium">GenAI RBAC</span>
          </div>
          <p className="text-xs text-slate-500 flex items-center gap-1">
            <Briefcase size={12} />
            <span>Active Scope: </span>
            <strong className="text-slate-700">{activeWorkspace?.name || 'Loading...'}</strong>
          </p>
        </div>
      </div>

      {/* Right controls: User Switcher & Info */}
      <div className="flex items-center space-x-4">
        {loading && (
          <span className="flex items-center text-xs text-slate-400 gap-1 animate-pulse">
            <RefreshCw size={12} className="animate-spin" /> Synchronizing...
          </span>
        )}

        <div className="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200">
          <div className="flex items-center px-2 py-1 text-xs font-medium text-slate-600 gap-1.5">
            <User size={14} className="text-slate-500" />
            <span>Demo User:</span>
          </div>

          <select
            value={currentUser?._id || ''}
            onChange={(e) => onSwitchUser(e.target.value)}
            className="bg-white border-0 text-xs font-semibold text-slate-800 rounded-md px-2.5 py-1 focus:ring-2 focus:ring-sky-500 shadow-xs cursor-pointer"
          >
            {demoUsers.map((u) => (
              <option key={u._id} value={u._id}>
                {u.full_name} ({u.role})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full font-medium">
          <Shield size={13} />
          <span>RBAC Guard Active</span>
        </div>
      </div>
    </header>
  );
}
