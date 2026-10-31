import React, { useState } from 'react';
import {
  X,
  UploadCloud,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  Eye,
  Plus,
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import { api } from '../services/api';

export default function DocumentLibraryModal({
  workspace,
  documents,
  onClose,
  onRefreshDocs,
  onSelectDocPreview
}) {
  const [showUpload, setShowUpload] = useState(false);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState('');
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadError('Please select a declared text-based file (.txt, .md, or .pdf).');
      return;
    }

    setUploading(true);
    setUploadProgress(20);
    setUploadStage('1/3: Uploading document to server...');
    setUploadError(null);
    setUploadSuccess(null);

    const timer1 = setTimeout(() => {
      setUploadProgress(60);
      setUploadStage('2/3: Parsing text structure & generating semantic chunks...');
    }, 400);

    const timer2 = setTimeout(() => {
      setUploadProgress(85);
      setUploadStage('3/3: Indexing embeddings into ChromaDB vector store...');
    }, 850);

    try {
      const res = await api.uploadDocument(workspace._id, file, title);
      clearTimeout(timer1);
      clearTimeout(timer2);
      setUploadProgress(100);
      setUploadStage('Complete!');
      setUploading(false);

      if (res.status === 'FAILED') {
        setUploadError(`Document ingestion failed: ${res.error_message}`);
      } else {
        setUploadSuccess(`Uploaded "${res.title}" successfully (Status: ${res.status}, ${res.chunk_count} chunks indexed).`);
        setFile(null);
        setTitle('');
        setTimeout(() => {
          setShowUpload(false);
          setUploadSuccess(null);
          setUploadProgress(0);
          setUploadStage('');
        }, 1600);
      }
      onRefreshDocs();
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setUploading(false);
      setUploadProgress(0);
      setUploadStage('');
      setUploadError(err.message || 'Failed to upload document');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 text-sm flex items-center gap-2">
              <FileText size={18} className="text-sky-600" />
              <span>Workspace Document Library</span>
            </h3>
            <p className="text-xs text-slate-500">
              Department / Workspace Scope: <strong className="text-slate-700">{workspace.name}</strong>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setShowUpload(!showUpload);
                setUploadError(null);
                setUploadSuccess(null);
              }}
              className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
            >
              <Plus size={14} />
              <span>{showUpload ? 'View Document List' : 'Upload Document'}</span>
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg transition-colors cursor-pointer"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Upload Form View */}
          {showUpload ? (
            <form onSubmit={handleUploadSubmit} className="max-w-lg mx-auto space-y-4 py-4">
              <div className="text-center mb-6">
                <h4 className="font-semibold text-slate-900 text-sm">Upload New Knowledge Document</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Supported formats: Text-based PDF (.pdf) or Plain Text (.txt, .md). Max size: 15 MB.
                </p>
              </div>

              {uploadError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3.5 rounded-lg text-xs flex items-start gap-2.5">
                  <AlertCircle size={16} className="text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block">Processing / Upload Failure</span>
                    <span>{uploadError}</span>
                  </div>
                </div>
              )}

              {uploadSuccess && (
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-lg text-xs flex items-center gap-2">
                  <CheckCircle size={16} className="text-emerald-600 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Document Title (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Q4 Infrastructure Blueprint"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Select File (.txt, .md, .pdf)
                </label>
                <input
                  type="file"
                  accept=".txt,.pdf,.md"
                  onChange={(e) => setFile(e.target.files[0] || null)}
                  className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 cursor-pointer border border-slate-300 rounded-lg"
                />
              </div>

              {/* Enhanced Upload Progress Indicator */}
              {uploading && (
                <div className="p-3.5 bg-sky-50 border border-sky-200 rounded-lg space-y-2">
                  <div className="flex items-center justify-between text-xs text-sky-900 font-medium">
                    <span className="flex items-center gap-1.5 font-semibold">
                      <RefreshCw size={13} className="animate-spin text-sky-600" />
                      {uploadStage}
                    </span>
                    <span className="font-mono text-sky-700 font-bold">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-sky-200 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-sky-600 h-full rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
                >
                  <UploadCloud size={14} />
                  <span>{uploading ? 'Processing Document...' : 'Upload & Index'}</span>
                </button>
              </div>
            </form>
          ) : (
            /* Documents Table View */
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{documents.length} documents registered in this workspace</span>
                <button
                  onClick={onRefreshDocs}
                  className="flex items-center gap-1 text-sky-600 hover:text-sky-700 font-medium cursor-pointer"
                >
                  <RefreshCw size={12} /> Refresh
                </button>
              </div>

              <div className="border border-slate-200 rounded-lg overflow-hidden shadow-2xs">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-3 px-4">Title / Filename</th>
                      <th className="py-3 px-4">Format</th>
                      <th className="py-3 px-4">Chunks</th>
                      <th className="py-3 px-4">Processing Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {documents.length === 0 ? (
                      /* Empty Document Library State */
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-slate-400">
                          <FolderOpen size={32} className="mx-auto mb-2 text-slate-300" />
                          <div className="font-semibold text-slate-600">No documents found in this workspace</div>
                          <div className="text-[11px] text-slate-400 mt-0.5">Click "Upload Document" above to ingest files.</div>
                        </td>
                      </tr>
                    ) : (
                      documents.map((doc) => {
                        const isIndexed = doc.status === 'INDEXED';
                        const isFailed = doc.status === 'FAILED';
                        return (
                          <tr key={doc._id} className="hover:bg-slate-50/70 transition-colors">
                            <td className="py-3 px-4">
                              <div className="font-semibold text-slate-900">{doc.title}</div>
                              <div className="text-[11px] text-slate-400">{doc.filename}</div>
                              {doc.error_message && (
                                <div className="text-[10px] text-rose-600 mt-0.5 flex items-center gap-1">
                                  <AlertCircle size={10} /> {doc.error_message}
                                </div>
                              )}
                            </td>
                            <td className="py-3 px-4 uppercase text-slate-600 font-mono">
                              {doc.filename.split('.').pop()}
                            </td>
                            <td className="py-3 px-4 text-slate-600 font-semibold">
                              {doc.chunk_count}
                            </td>
                            <td className="py-3 px-4">
                              {isIndexed && (
                                <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
                                  <CheckCircle size={11} /> Indexed
                                </span>
                              )}
                              {isFailed && (
                                <span className="inline-flex items-center gap-1 bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
                                  <AlertCircle size={11} /> Failed
                                </span>
                              )}
                              {!isIndexed && !isFailed && (
                                <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
                                  <Clock size={11} /> Processing
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={() => onSelectDocPreview(doc._id)}
                                disabled={!isIndexed}
                                title={isFailed ? 'Cannot preview failed document' : !isIndexed ? 'Document is still processing' : 'Preview document content and chunks'}
                                className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md transition-colors ${
                                  !isIndexed
                                    ? 'opacity-40 text-slate-400 cursor-not-allowed'
                                    : 'text-sky-700 hover:text-sky-900 bg-sky-50 hover:bg-sky-100 cursor-pointer'
                                }`}
                              >
                                <Eye size={12} />
                                <span>{isFailed ? 'Failed' : !isIndexed ? 'Pending' : 'Preview'}</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 flex justify-between items-center text-xs text-slate-500">
          <span>Accessible strictly to authorized workspace members.</span>
          <button
            onClick={onClose}
            className="text-xs font-medium text-slate-600 hover:text-slate-800 px-3 py-1.5 rounded-lg cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
