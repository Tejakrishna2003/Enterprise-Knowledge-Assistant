import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bookmark,
  AlertCircle,
  HelpCircle,
  Clock,
  ArrowRight,
  Layers,
  FileText,
  AlertTriangle,
  RotateCcw,
  X
} from 'lucide-react';

export default function ChatWorkspace({
  conversation,
  messages,
  onSendMessage,
  onInspectCitation,
  activeWorkspace,
  sending,
  error,
  onDismissError
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleSuggestionClick = (query) => {
    setInput(query);
  };

  return (
    <main className="flex-1 flex flex-col h-full bg-slate-50 relative overflow-hidden">
      {/* Top Bar for Chat Header */}
      <div className="h-12 border-b border-slate-200 bg-white/70 backdrop-blur-xs px-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <span className="font-semibold text-slate-800">
            {conversation?.title || 'New Conversation'}
          </span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-500">{messages.length} messages</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-sky-700 bg-sky-50 border border-sky-200/80 px-2 py-0.5 rounded-full font-medium">
          <Layers size={12} />
          <span>Scope: {activeWorkspace?.name}</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          /* Empty State with Pre-built Evaluation Questions */
          <div className="max-w-2xl mx-auto py-12 text-center space-y-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white flex items-center justify-center mx-auto shadow-md shadow-sky-500/20">
              <Sparkles size={26} />
            </div>

            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Enterprise Knowledge Assistant
              </h2>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                Ask questions grounded strictly in authorized documents. All answers are cited back to verified sections.
              </p>
            </div>

            {/* Prompt Cards */}
            <div className="text-left space-y-2.5 max-w-xl mx-auto pt-2">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Recommended Evaluation Scenarios
              </div>

              {/* Scenario 1: Multi-Doc */}
              <button
                onClick={() => handleSuggestionClick("When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?")}
                className="w-full text-left p-3.5 bg-white border border-slate-200 hover:border-sky-400 rounded-xl transition-all shadow-2xs hover:shadow-xs group cursor-pointer"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-1">
                  <span className="text-sky-700 font-bold">1. Multi-Document Synthesis</span>
                  <ArrowRight size={13} className="text-slate-400 group-hover:text-sky-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-600">
                  "When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?"
                </p>
              </button>

              {/* Scenario 2: Follow-up */}
              <button
                onClick={() => handleSuggestionClick("Who has the authority to bypass those drain timers during this rollback?")}
                className="w-full text-left p-3.5 bg-white border border-slate-200 hover:border-sky-400 rounded-xl transition-all shadow-2xs hover:shadow-xs group cursor-pointer"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-1">
                  <span className="text-indigo-700 font-bold">2. Follow-Up Continuity</span>
                  <ArrowRight size={13} className="text-slate-400 group-hover:text-indigo-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-600">
                  "Who has the authority to bypass those drain timers during this rollback?"
                </p>
              </button>

              {/* Scenario 3: Unsupported */}
              <button
                onClick={() => handleSuggestionClick("What is our company's refund policy for enterprise customer subscription cancellations in Germany?")}
                className="w-full text-left p-3.5 bg-white border border-slate-200 hover:border-rose-400 rounded-xl transition-all shadow-2xs hover:shadow-xs group cursor-pointer"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-1">
                  <span className="text-rose-700 font-bold">3. Unsupported / Missing Evidence Test</span>
                  <ArrowRight size={13} className="text-slate-400 group-hover:text-rose-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <p className="text-xs text-slate-600">
                  "What is our company's refund policy for enterprise customer subscription cancellations in Germany?"
                </p>
              </button>
            </div>
          </div>
        ) : (
          /* Messages Stream */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, idx) => {
              const isUser = msg.sender === 'user';
              const isFailed = msg.status === 'FAILED';
              const isUnsupported = !isUser && (!msg.citations || msg.citations.length === 0) && !isFailed;

              return (
                <div
                  key={msg.id || idx}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 shadow-xs mt-1 ${
                      isFailed ? 'bg-rose-600 text-white' : 'bg-sky-600 text-white'
                    }`}>
                      AI
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed shadow-2xs ${
                      isUser
                        ? 'bg-sky-600 text-white rounded-br-xs'
                        : isFailed
                        ? 'bg-rose-50 border border-rose-200 text-rose-900 rounded-bl-xs'
                        : isUnsupported
                        ? 'bg-amber-50/70 border border-amber-200 text-slate-800 rounded-bl-xs'
                        : 'bg-white border border-slate-200/90 text-slate-800 rounded-bl-xs'
                    }`}
                  >
                    {/* Unsupported notice badge */}
                    {isUnsupported && (
                      <div className="mb-2 pb-2 border-b border-amber-200/70 text-[11px] font-semibold text-amber-800 flex items-center gap-1.5">
                        <AlertTriangle size={13} className="text-amber-600" />
                        <span>Evidence Absent from Workspace Documentation</span>
                      </div>
                    )}

                    {/* User Question or Assistant Output */}
                    <div className="whitespace-pre-wrap select-text">
                      {msg.content}
                    </div>

                    {/* Failure State Card */}
                    {isFailed && (
                      <div className="mt-3 pt-2.5 border-t border-rose-200/60 text-[11px] text-rose-700 flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-medium">
                          <AlertCircle size={13} />
                          <span>Model execution failed. No ungrounded response was finalized.</span>
                        </div>
                        <button
                          onClick={() => {
                            const prevUserMsg = messages.slice(0, idx).reverse().find(m => m.sender === 'user');
                            if (prevUserMsg) onSendMessage(prevUserMsg.content);
                          }}
                          className="flex items-center gap-1 text-rose-700 hover:text-rose-900 font-bold underline cursor-pointer"
                        >
                          <RotateCcw size={11} /> Retry
                        </button>
                      </div>
                    )}

                    {/* Citation Pills (Only for assistant messages with citations) */}
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3.5 pt-3 border-t border-slate-100 space-y-2">
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                          <Bookmark size={12} className="text-sky-600" />
                          <span>Grounded Source Citations ({msg.citations.length})</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {msg.citations.map((c, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() => onInspectCitation(c)}
                              className="inline-flex items-center gap-1.5 bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200/80 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold transition-all hover:shadow-xs cursor-pointer group"
                            >
                              <FileText size={12} className="text-sky-600 group-hover:scale-110 transition-transform" />
                              <span className="truncate max-w-[200px]">{c.document_title}</span>
                              <span className="text-[10px] bg-sky-200/70 text-sky-900 px-1 rounded-sm">
                                p.{c.page_number || 1}
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-lg bg-slate-800 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs mt-1">
                      U
                    </div>
                  )}
                </div>
              );
            })}

            {/* Pulsing indicator when waiting for AI answer */}
            {sending && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-lg bg-sky-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs mt-1 animate-pulse">
                  AI
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl p-4 text-xs text-slate-500 flex items-center gap-2 rounded-bl-xs shadow-2xs">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-sky-500 animate-bounce"></span>
                    <span className="w-2 h-2 rounded-full bg-sky-500 animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-2 h-2 rounded-full bg-sky-500 animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                  <span>Retrieving workspace chunks & verifying citations...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error Callout Banner */}
      {error && (
        <div className="bg-rose-50 border-t border-rose-200 px-6 py-2.5 text-xs text-rose-800 flex items-center justify-between animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <AlertCircle size={15} className="text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => onDismissError && onDismissError()}
            className="text-rose-500 hover:text-rose-700 p-0.5 rounded-sm cursor-pointer"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Bottom Query Input Box */}
      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask a question in ${activeWorkspace?.name || 'this workspace'}...`}
            disabled={sending}
            className="flex-1 text-xs px-4 py-3 bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-2 focus:ring-sky-500 focus:outline-hidden disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || sending}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white px-5 py-3 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
          >
            <Send size={14} />
            <span>Send</span>
          </button>
        </form>
      </div>
    </main>
  );
}
