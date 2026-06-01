import React, { useState, useRef, useEffect, useCallback } from 'react';
import { chatWithAI, getChatHistory } from './api';

// FIX: safe markdown renderer — no dangerouslySetInnerHTML / XSS risk
function SafeMarkdown({ text }) {
  // Convert **bold** and newlines only; output as plain React nodes
  const parts = text.split(/(\*\*.*?\*\*|\n)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part === '\n') return <br key={i} />;
        if (part.startsWith('**') && part.endsWith('**'))
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        return part;
      })}
    </>
  );
}

// FIX: props simplified — name/age/height/weight no longer needed here;
//      the backend fetches them from the DB using faceId
function ChatComponent({ name, faceId }) {
  // FIX: start with empty array; greeting is set AFTER history load
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(scrollToBottom, [messages]);

  // FIX: load history, then fall back to greeting only when history is empty
  useEffect(() => {
    if (!faceId) return;
    const loadHistory = async () => {
      try {
        const res = await getChatHistory(faceId);
        if (res.data && res.data.length > 0) {
          setMessages(
            res.data.map((msg) => ({ sender: msg.role, text: msg.content }))
          );
        } else {
          // No history yet — show a fresh greeting
          setMessages([
            {
              sender: 'ai',
              text: `Hi ${name}! I'm your personal AI diet coach. How can I help you today?`,
            },
          ]);
        }
      } catch (err) {
        console.error('Failed to load history:', err);
        // Still show a greeting so the UI isn't blank
        setMessages([
          {
            sender: 'ai',
            text: `Hi ${name}! I'm your personal AI diet coach. How can I help you today?`,
          },
        ]);
      }
    };
    loadHistory();
  }, [faceId, name]);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setInput('');
    setIsLoading(true);
    try {
      // FIX: only pass message + faceId — no stats re-sent
      const res = await chatWithAI(userMsg, faceId);
      setMessages((prev) => [
        ...prev,
        { sender: 'ai', text: res.data.response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: 'ai', text: 'Sorry, I had trouble thinking about that. Please try again.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [input, faceId]);

  return (
    <div className="flex flex-col h-[600px] w-full bg-white rounded-3xl overflow-hidden shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-slate-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm p-5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/30">
            AI
          </div>
          <div>
            <h3 className="font-bold text-lg text-slate-800">FitAi Coach</h3>
            <p className="text-xs text-green-500 font-medium flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Online &amp; Ready
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-5 py-4 text-sm leading-relaxed shadow-sm ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-white text-slate-600 border border-slate-200 rounded-tl-none'
              }`}
            >
              {/* FIX: SafeMarkdown instead of dangerouslySetInnerHTML */}
              <SafeMarkdown text={msg.text} />
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-white text-slate-400 border border-slate-100 rounded-2xl px-5 py-3 rounded-tl-none text-sm italic shadow-sm">
              Generating your plan...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-slate-100">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
            placeholder="Type 'Make me a plan'..."
            className="flex-1 bg-slate-50 text-slate-800 rounded-2xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:bg-white transition-all placeholder:text-slate-400"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-2xl px-8 font-bold shadow-lg shadow-blue-500/30 disabled:opacity-50 disabled:shadow-none transition-all hover:-translate-y-0.5"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatComponent;
