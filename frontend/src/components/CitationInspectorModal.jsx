import React from 'react';
import { X, BookOpen, FileText, ExternalLink, Bookmark } from 'lucide-react';

export default function CitationInspectorModal({ citation, onClose, onOpenDocument }) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-xl w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-50 border-b border-slate-200 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sky-700">
            <Bookmark size={18} />
            <h3 className="font-semibold text-slate-900 text-sm">Grounded Source Evidence</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Source Document
            </span>
            <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <FileText size={16} className="text-sky-600 shrink-0" />
              <span>{citation.document_title}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs">
            <div>
              <span className="text-slate-400 block font-medium">Section / Topic:</span>
              <span className="font-semibold text-slate-700">{citation.section_title || 'General'}</span>
            </div>
            <div>
              <span className="text-slate-400 block font-medium">Page Number:</span>
              <span className="font-semibold text-slate-700">Page {citation.page_number || 1}</span>
            </div>
          </div>

          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
              Verified Evidence Snippet
            </span>
            <div className="bg-sky-50/60 border-l-4 border-sky-500 p-4 rounded-r-lg text-xs leading-relaxed text-slate-800 italic font-serif">
              "{citation.snippet}"
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-5 py-3 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">Verified by ChromaDB Vector Grounding</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onOpenDocument(citation.document_id)}
              className="flex items-center gap-1.5 text-xs font-semibold text-sky-700 hover:text-sky-800 bg-sky-100/70 hover:bg-sky-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
            >
              <ExternalLink size={13} />
              <span>Open Document Preview</span>
            </button>
            <button
              onClick={onClose}
              className="text-xs font-medium text-slate-600 hover:text-slate-800 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
