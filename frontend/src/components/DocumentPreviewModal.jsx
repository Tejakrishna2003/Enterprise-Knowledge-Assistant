import React, { useEffect, useState } from 'react';
import { X, FileText, CheckCircle, AlertTriangle, Layers, Calendar, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function DocumentPreviewModal({ documentId, workspaceId, onClose }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocument = () => {
    if (!documentId || !workspaceId) return;
    setLoading(true);
    setError(null);
    api.getDocumentDetail(workspaceId, documentId)
      .then((data) => {
        setDoc(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load document content.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDocument();
  }, [documentId, workspaceId]);

  if (!documentId) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sky-100 text-sky-700 rounded-lg">
              <FileText size={20} />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">
                {doc?.title || 'Document Content Preview'}
              </h3>
              <p className="text-xs text-slate-500">{doc?.filename || 'Loading...'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg transition-colors cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center text-slate-400 text-xs gap-3">
              <RefreshCw size={24} className="animate-spin text-sky-600" />
              <span>Fetching document content and indexed chunks...</span>
            </div>
          )}

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-lg text-xs space-y-2">
              <div className="flex items-center gap-2 font-semibold">
                <AlertCircle size={16} className="text-rose-600 shrink-0" />
                <span>Failed to Load Document Content</span>
              </div>
              <p className="text-rose-700">{error}</p>
              <button
                onClick={fetchDocument}
                className="mt-2 text-xs font-semibold bg-rose-600 text-white px-3 py-1.5 rounded-md hover:bg-rose-500 transition cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {doc && !loading && (
            <>
              {/* Metadata Pills */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-md font-medium flex items-center gap-1">
                  <CheckCircle size={13} /> Status: {doc.status}
                </span>
                <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium flex items-center gap-1">
                  <Layers size={13} /> {doc.chunk_count} Indexed Chunks
                </span>
                <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium">
                  Size: {(doc.file_size / 1024).toFixed(1)} KB
                </span>
              </div>

              {/* Raw Document Content Display */}
              <div className="border border-slate-200 rounded-lg bg-slate-50/50 p-5 font-mono text-xs leading-relaxed text-slate-800 whitespace-pre-wrap select-text max-h-[50vh] overflow-y-auto">
                {doc.raw_content || 'No text extracted from document.'}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 flex justify-end">
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
