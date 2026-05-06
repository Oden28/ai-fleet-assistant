import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useCopilot } from '../../hooks/useFleetData';
import TopBar from '../../components/Layout/TopBar';
import { Send, Bot, User, BookOpen, Database, AlertCircle, Sparkles, MessageCircle } from 'lucide-react';
import './Copilot.css';

const SUGGESTED_PROMPTS = [
  { text: 'Why did VH-G-123 trigger a battery alert?', icon: AlertCircle },
  { text: 'Show me vehicles with high fuel consumption.', icon: Database },
  { text: 'Which drivers have the most harsh events?', icon: User },
  { text: 'Summarize alerts in the North region this week.', icon: BookOpen },
  { text: 'What does error code E104 mean?', icon: Sparkles },
  { text: 'Which 5 assets had the highest idle time?', icon: Database },
];

export default function Copilot() {
  const [searchParams] = useSearchParams();
  const { messages, loading, ask, clear } = useCopilot();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Pre-fill from URL context
  useEffect(() => {
    const q = searchParams.get('q');
    const contextId = searchParams.get('id');
    if (q) {
      setInput(q);
    }
    if (contextId) {
      setInput(prev => prev || `Tell me about asset ${contextId}`);
    }
  }, [searchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const q = input.trim();
    if (!q || loading) return;
    const context = searchParams.get('context') === 'vehicle'
      ? { vehicle_id: searchParams.get('id'), screen: 'vehicle_detail' }
      : null;
    ask(q, context);
    setInput('');
  };

  const handlePrompt = (text) => {
    ask(text);
    setInput('');
  };

  return (
    <>
      <TopBar
        title="AI Copilot"
        showBack
        right={
          messages.length > 0 && (
            <button className="btn btn-ghost" onClick={clear} style={{ fontSize: 12 }}>
              <MessageCircle size={14} /> New chat
            </button>
          )
        }
      />
      <div className="copilot-page page-with-topbar">
        {/* Empty state */}
        {messages.length === 0 && (
          <div className="copilot-empty animate-fade-in">
            <div className="copilot-logo">
              <Bot size={32} />
            </div>
            <h2>How can I help you today?</h2>
            <p>Ask about your fleet, assets, data or technical issues.</p>

            <div className="copilot-input-area copilot-input-center">
              <input
                ref={inputRef}
                className="input copilot-input"
                placeholder="Ask anything..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              />
              <button className="copilot-send" onClick={handleSend} disabled={loading || !input.trim()}>
                <Send size={18} />
              </button>
            </div>

            <div className="copilot-prompts">
              <h3>Try asking</h3>
              {SUGGESTED_PROMPTS.map((p, i) => (
                <button key={i} className="copilot-prompt-btn" onClick={() => handlePrompt(p.text)}>
                  <p.icon size={14} />
                  {p.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.length > 0 && (
          <div className="copilot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`copilot-msg copilot-msg-${msg.role} animate-slide-up`}>
                <div className="copilot-msg-avatar">
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className="copilot-msg-body">
                  {msg.role === 'user' ? (
                    <p>{msg.content}</p>
                  ) : msg.role === 'error' ? (
                    <div className="copilot-error">
                      <AlertCircle size={14} /> {msg.content}
                    </div>
                  ) : (
                    <>
                      <div className="copilot-answer">{msg.content}</div>

                      {msg.confidence && (
                        <span className={`badge badge-${msg.confidence === 'high' ? 'success' : msg.confidence === 'medium' ? 'warning' : 'critical'}`}
                          style={{ marginTop: 8, display: 'inline-block' }}>
                          Confidence: {msg.confidence}
                        </span>
                      )}

                      {msg.sources?.length > 0 && (
                        <div className="copilot-sources">
                          <strong>Sources:</strong> {msg.sources.join(', ')}
                        </div>
                      )}

                      {msg.caveats?.length > 0 && (
                        <div className="copilot-caveats">
                          {msg.caveats.map((c, j) => (
                            <div key={j} className="copilot-caveat">⚠️ {c}</div>
                          ))}
                        </div>
                      )}

                      {msg.artifacts?.length > 0 && (
                        <details className="copilot-artifacts">
                          <summary>Query Logic</summary>
                          {msg.artifacts.map((a, j) => (
                            <pre key={j} className="copilot-code">{a.content}</pre>
                          ))}
                        </details>
                      )}

                      {msg.is_clarification && (
                        <div className="copilot-clarification">
                          <Sparkles size={14} /> This is a clarification request — please provide more details.
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="copilot-msg copilot-msg-assistant animate-fade-in">
                <div className="copilot-msg-avatar"><Bot size={16} /></div>
                <div className="copilot-msg-body">
                  <div className="copilot-typing">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Bottom input (when in chat mode) */}
        {messages.length > 0 && (
          <div className="copilot-bottom-input">
            <div className="copilot-input-area">
              <input
                className="input copilot-input"
                placeholder="Ask a follow-up..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              />
              <button className="copilot-send" onClick={handleSend} disabled={loading || !input.trim()}>
                <Send size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
