import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DashboardLayout from '../components/DashboardLayout';
import {
  Bot,
  Send,
  Sparkles,
  Mic,
  RotateCcw,
  BookOpen,
  Zap,
  CheckCircle2,
  ArrowRight,
  Lightbulb,
  FileText,
  HelpCircle,
  Clock,
  Info,
  Layers,
  BrainCircuit,
  Upload,
  Copy,
  Check,
  AlertCircle
} from 'lucide-react';
import {
  getSubjectsProgress,
  getChatHistory,
  clearChatHistory,
  sendChatMessageStream
} from '../services/api';
import { useAuth } from '../context/AuthContext';

// Helper component for Code Blocks with syntax label & Copy button
function CodeBlock({ node, inline, className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || '');
  const codeString = String(children).replace(/\n$/, '');
  const [copied, setCopied] = useState(false);

  const handleCopy = (e) => {
    e.preventDefault();
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!inline && (match || codeString.includes('\n'))) {
    const lang = match ? match[1] : 'code';
    return (
      <div className="code-block-wrapper">
        <div className="code-block-header">
          <span className="code-lang-label">{lang}</span>
          <button
            type="button"
            onClick={handleCopy}
            className="code-copy-btn"
            title="Copy code to clipboard"
          >
            {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
        </div>
        <pre className="code-block-pre">
          <code className={className} {...props}>
            {children}
          </code>
        </pre>
      </div>
    );
  }

  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
}

export default function AiAssistantPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [activeSubject, setActiveSubject] = useState(null);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [chatError, setChatError] = useState(null);
  const [lastFailedPrompt, setLastFailedPrompt] = useState(null);

  // Web Speech API Voice-to-Text State
  const [micActive, setMicActive] = useState(false);
  const speechRecognitionSupported = typeof window !== 'undefined' && Boolean(
    window.SpeechRecognition || window.webkitSpeechRecognition
  );
  const recognitionRef = useRef(null);

  const chatBottomRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Load subject context & authenticated conversation history from SQLite
  useEffect(() => {
    async function loadInitialData() {
      setLoadingHistory(true);
      try {
        const [subjRes, historyRes] = await Promise.all([
          getSubjectsProgress(),
          getChatHistory()
        ]);

        if (subjRes.success && Array.isArray(subjRes.data) && subjRes.data.length > 0) {
          setActiveSubject(subjRes.data[0]);
        }

        if (historyRes.success && historyRes.data?.messages) {
          const loaded = historyRes.data.messages.map((m) => ({
            id: m.id,
            sender: m.role === 'user' ? 'user' : 'ai',
            text: m.content,
            time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }));
          setMessages(loaded);
        }
      } catch (err) {
        console.warn('Failed to load initial assistant data:', err);
      } finally {
        setLoadingHistory(false);
      }
    }

    loadInitialData();
  }, []);

  // Auto-scroll to bottom as new tokens arrive
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Clean up speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Starter Suggestion Cards
  const suggestionCards = [
    {
      title: "Explain a difficult concept",
      prompt: "Explain Binary Search with step-by-step example and time complexity.",
      icon: Lightbulb,
      bg: "#eef2ff",
      color: "#4f46e5"
    },
    {
      title: "Compare topics",
      prompt: "Stack aur Queue mein kya difference hai? Real life example ke sath samjhao.",
      icon: Layers,
      bg: "#f5f3ff",
      color: "#7c3aed"
    },
    {
      title: "Practice questions",
      prompt: "Create 3 practice quiz questions on Database Normalization with explanations.",
      icon: Zap,
      bg: "#f0f9ff",
      color: "#0ea5e9"
    },
    {
      title: "Exam preparation tips",
      prompt: "How should I structure my answers for semester engineering exams?",
      icon: BookOpen,
      bg: "#ecfdf5",
      color: "#10b981"
    }
  ];

  // Dynamic Quick Prompt Chips applying to previous response or current topic
  const quickChips = [
    { label: "Explain simply", type: "explain_simply" },
    { label: "Give an example", type: "give_example" },
    { label: "Summarize", type: "summarize" },
    { label: "Create quiz questions", type: "quiz_questions" }
  ];

  const handleQuickPromptClick = (type) => {
    if (isTyping) return;

    const lastUserMsg = [...messages].reverse().find(m => m.sender === 'user');
    const targetTopic = activeSubject?.current_topic && activeSubject.current_topic !== 'Not started yet'
      ? activeSubject.current_topic
      : (activeSubject?.name || '');

    let query = '';
    switch (type) {
      case 'explain_simply':
        query = lastUserMsg
          ? 'Is topic ko aur simple shabdon mein samjhao ek aasan analogy/example ke sath.'
          : targetTopic
          ? `Explain ${targetTopic} in very simple terms with a real-life analogy.`
          : 'Can you explain this concept in simpler words with a daily life example?';
        break;
      case 'give_example':
        query = lastUserMsg
          ? 'Iska ek practical real-life example ya code demo dikhao comments ke sath.'
          : targetTopic
          ? `Give me a practical real-world example and code demo of ${targetTopic}.`
          : 'Please provide a clear real-world example and practical code demo for this.';
        break;
      case 'summarize':
        query = lastUserMsg
          ? 'Is pure concept ko 3-4 crisp bullet points mein summarize karo quick exam revision ke liye.'
          : targetTopic
          ? `Summarize the key points and formulas for ${targetTopic}.`
          : 'Summarize the core takeaways and key definitions in quick bullet points.';
        break;
      case 'quiz_questions':
        query = lastUserMsg
          ? 'Is topic par 3 practice multiple-choice questions banao options, answers aur explanations ke sath.'
          : targetTopic
          ? `Create 3 practice quiz questions on ${targetTopic} with options and detailed explanations.`
          : 'Create 3 practice quiz questions on this topic with options, correct answers and explanations.';
        break;
      default:
        query = type;
    }

    handleSend(query);
  };

  // Send message with real-time streaming via official Google Gen AI SDK
  const handleSend = async (textToSend = input) => {
    const query = textToSend.trim();
    if (!query || isTyping) return;

    if (query.length > 4000) {
      setChatError('Message exceeds maximum limit of 4000 characters.');
      return;
    }

    setChatError(null);
    setLastFailedPrompt(null);

    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. Add user query to chat window
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: query,
      time: currentTime
    };

    const aiMessageId = Date.now() + 1;
    const aiPlaceholder = {
      id: aiMessageId,
      sender: 'ai',
      text: '',
      time: currentTime
    };

    setMessages((prev) => [...prev, userMessage, aiPlaceholder]);
    setInput('');
    setIsTyping(true);

    // Prepare multi-turn history payload (last 14 messages)
    const historyPayload = messages.slice(-14).map((m) => ({
      role: m.sender === 'user' ? 'user' : 'model',
      content: m.text
    }));

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let accumulatedText = '';

    await sendChatMessageStream({
      message: query,
      subject_code: activeSubject?.code || null,
      subject_name: activeSubject?.name || null,
      topic: activeSubject?.current_topic || null,
      history: historyPayload,
      signal: controller.signal,
      onChunk: (chunkText) => {
        accumulatedText += chunkText;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId ? { ...msg, text: accumulatedText } : msg
          )
        );
      },
      onComplete: () => {
        setIsTyping(false);
      },
      onError: (errMsg) => {
        setIsTyping(false);
        setChatError(errMsg);
        setLastFailedPrompt(query);
        // Remove empty placeholder if nothing was streamed
        if (!accumulatedText) {
          setMessages((prev) => prev.filter((msg) => msg.id !== aiMessageId));
        }
      }
    });
  };

  // Clear chat conversation
  const handleClearChat = async () => {
    if (isTyping) return;
    try {
      await clearChatHistory();
      setMessages([]);
      setChatError(null);
      setLastFailedPrompt(null);
    } catch {
      setMessages([]);
    }
  };

  // Browser Web Speech API Voice-to-Text
  const handleMicClick = () => {
    if (!speechRecognitionSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (micActive) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setMicActive(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-IN';
      recognition.interimResults = true;
      recognition.continuous = false;

      recognition.onstart = () => {
        setMicActive(true);
      };

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((result) => result[0].transcript)
          .join('');
        setInput(transcript);
      };

      recognition.onerror = () => {
        setMicActive(false);
      };

      recognition.onend = () => {
        setMicActive(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn('Speech recognition start failed:', err);
      setMicActive(false);
    }
  };

  return (
    <DashboardLayout>
      {/* 1. Page Header */}
      <div className="ai-page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>AI Study Assistant</h1>
            <span className="badge badge-primary">
              <Sparkles size={13} />
              <span>Google Gemini AI</span>
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Ask questions, understand concepts, and get step-by-step guidance.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={handleClearChat}
            disabled={messages.length === 0 || isTyping}
            className="btn btn-secondary btn-sm"
            title="Clear conversation history from database"
          >
            <RotateCcw size={14} />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Chat Workspace + Right Side Study Context */}
      <div className="ai-workspace-layout">
        {/* Chat Main Column */}
        <div className="ai-chat-column">
          {/* Welcome Area Suggestion Cards (Shown when chat is empty and not loading) */}
          {!loadingHistory && messages.length === 0 && (
            <div className="ai-welcome-box">
              <div className="welcome-headline">
                <div className="brand-icon" style={{ width: 42, height: 42 }}>
                  <BrainCircuit size={22} />
                </div>
                <div>
                  <h3>What would you like to learn today?</h3>
                  <p>
                    Ask EduMind AI to explain concepts, simplify difficult topics, solve doubt questions, or prepare for exams.
                  </p>
                </div>
              </div>

              <div className="suggestions-grid">
                {suggestionCards.map((card, idx) => {
                  const Icon = card.icon;
                  return (
                    <button
                      key={idx}
                      className="suggestion-card-btn"
                      onClick={() => handleSend(card.prompt)}
                      disabled={isTyping}
                    >
                      <div className="suggestion-icon" style={{ backgroundColor: card.bg, color: card.color }}>
                        <Icon size={18} />
                      </div>
                      <span className="suggestion-title">{card.title}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Chat Container Card */}
          <div className="ai-chat-card">
            {/* Chat Card Header */}
            <div className="ai-chat-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div className="brand-icon" style={{ width: 32, height: 32 }}>
                  <Bot size={17} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.92rem', fontWeight: 700, margin: 0 }}>EduMind Study Bot</h4>
                  <span style={{ fontSize: '0.74rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }} />
                    Active Learning Session
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {activeSubject && (
                  <span className="badge badge-primary" style={{ fontSize: '0.72rem' }}>
                    Context: {activeSubject.name}
                  </span>
                )}
              </div>
            </div>

            {/* Chat Message Scroll Window */}
            <div className="ai-chat-messages-window">
              {messages.map((msg) => (
                <div key={msg.id} className={`ai-message-row ${msg.sender === 'user' ? 'msg-user' : 'msg-ai'}`}>
                  {msg.sender === 'ai' && (
                    <div className="ai-msg-avatar">
                      <Bot size={16} />
                    </div>
                  )}

                  <div className="ai-msg-content-box">
                    <div className="ai-bubble-body">
                      {msg.sender === 'ai' ? (
                        <div className="chat-markdown">
                          {msg.text ? (
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                code: CodeBlock
                              }}
                            >
                              {msg.text}
                            </ReactMarkdown>
                          ) : (
                            <div className="typing-indicator" style={{ padding: '0.2rem 0' }}>
                              <span className="dot" />
                              <span className="dot" />
                              <span className="dot" />
                              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '0.4rem' }}>
                                EduMind AI is thinking...
                              </span>
                            </div>
                          )}
                        </div>
                      ) : (
                        msg.text
                      )}
                    </div>
                    <span className="ai-msg-timestamp">{msg.time}</span>
                  </div>
                </div>
              ))}

              {/* Friendly Error Banner with Retry */}
              {chatError && (
                <div className="chat-error-banner">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <AlertCircle size={17} color="#ef4444" style={{ flexShrink: 0 }} />
                    <span>{chatError}</span>
                  </div>
                  {lastFailedPrompt && (
                    <button
                      type="button"
                      onClick={() => handleSend(lastFailedPrompt)}
                      disabled={isTyping}
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '0.25rem 0.65rem', fontSize: '0.78rem', whiteSpace: 'nowrap' }}
                    >
                      <RotateCcw size={13} />
                      <span>Retry</span>
                    </button>
                  )}
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Quick Prompt Chips */}
            <div className="ai-quick-chips-bar">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginRight: '0.2rem' }}>
                Quick Prompts:
              </span>
              {quickChips.map((chip, i) => (
                <button
                  key={i}
                  type="button"
                  className="quick-chip-btn"
                  onClick={() => handleQuickPromptClick(chip.type)}
                  disabled={isTyping}
                >
                  💡 {chip.label}
                </button>
              ))}
            </div>

            {/* Input Box */}
            <form
              className="ai-chat-input-container"
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
            >
              {/* Web Speech API Mic Button (Auto-hidden if browser lacks support) */}
              {speechRecognitionSupported && (
                <button
                  type="button"
                  className={`mic-btn ${micActive ? 'mic-listening' : ''}`}
                  onClick={handleMicClick}
                  title={micActive ? "Listening (click to stop)..." : "Voice Input (Speech to text)"}
                  disabled={isTyping}
                >
                  <Mic size={18} />
                </button>
              )}

              <input
                type="text"
                className="ai-chat-input-field"
                placeholder={
                  micActive
                    ? "Listening... speak now"
                    : "Ask EduMind AI anything about your studies (English, Hindi, Hinglish)..."
                }
                value={input}
                maxLength={4000}
                onChange={(e) => setInput(e.target.value)}
                disabled={isTyping}
              />

              <button
                type="submit"
                className="btn btn-primary"
                style={{ padding: '0.65rem 1.25rem', borderRadius: 'var(--radius-md)' }}
                disabled={!input.trim() || isTyping}
              >
                <Send size={16} />
                <span>{isTyping ? 'Answering...' : 'Send'}</span>
              </button>
            </form>
          </div>
        </div>

        {/* 7. Right Side / Study Context Panel */}
        <aside className="ai-study-context-panel">
          <div className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
              <div className="brand-icon" style={{ width: 32, height: 32, borderRadius: 8 }}>
                <Layers size={17} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>Study Context</h3>
            </div>

            <div className="context-item-group">
              {activeSubject ? (
                <>
                  <div className="context-item">
                    <span className="context-label">Current Subject</span>
                    <p className="context-value">{activeSubject.name}</p>
                    {activeSubject.code && (
                      <span className="badge badge-primary" style={{ marginTop: '0.3rem', fontSize: '0.72rem' }}>
                        {activeSubject.code}
                      </span>
                    )}
                  </div>

                  <div className="context-item" style={{ marginTop: '1rem' }}>
                    <span className="context-label">Current Topic</span>
                    <p className="context-value">{activeSubject.current_topic || 'Not started yet'}</p>
                  </div>

                  <div className="context-item" style={{ marginTop: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                      <span className="context-label" style={{ margin: 0 }}>Progress</span>
                      <span style={{ color: 'var(--primary)' }}>{activeSubject.progress || 0}%</span>
                    </div>
                    <div className="progress-track" style={{ height: 8 }}>
                      <div className="progress-fill" style={{ width: `${activeSubject.progress || 0}%`, backgroundColor: 'var(--primary)' }} />
                    </div>
                  </div>

                  <div className="context-suggestion-card" style={{ marginTop: '1.5rem' }}>
                    <span style={{ fontSize: '0.74rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary)', letterSpacing: '0.04em' }}>
                      Suggested Next Step
                    </span>
                    <h5 style={{ fontSize: '0.92rem', fontWeight: 700, margin: '0.4rem 0 0.85rem' }}>
                      {activeSubject.progress > 0 ? `Practice ${activeSubject.name} Questions` : `Read ${activeSubject.name} Material`}
                    </h5>
                    <button
                      onClick={() => navigate(activeSubject.progress > 0 ? '/quizzes' : '/materials')}
                      className="btn btn-primary"
                      style={{ width: '100%', fontSize: '0.88rem', padding: '0.6rem', justifyContent: 'center' }}
                    >
                      <Zap size={16} />
                      <span>{activeSubject.progress > 0 ? 'Start Quiz' : 'View Materials'}</span>
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="context-item">
                    <span className="context-label">Current Subject</span>
                    <p className="context-value" style={{ color: 'var(--text-muted)' }}>No subjects yet</p>
                  </div>

                  <div className="context-item" style={{ marginTop: '1rem' }}>
                    <span className="context-label">Current Topic</span>
                    <p className="context-value" style={{ color: 'var(--text-muted)' }}>Not started yet</p>
                  </div>

                  <div className="context-item" style={{ marginTop: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                      <span className="context-label" style={{ margin: 0 }}>Progress</span>
                      <span style={{ color: 'var(--text-muted)' }}>0%</span>
                    </div>
                    <div className="progress-track" style={{ height: 8 }}>
                      <div className="progress-fill" style={{ width: '0%', backgroundColor: 'var(--primary)' }} />
                    </div>
                  </div>

                  <div className="context-suggestion-card" style={{ marginTop: '1.5rem' }}>
                    <span style={{ fontSize: '0.74rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary)', letterSpacing: '0.04em' }}>
                      Getting Started
                    </span>
                    <h5 style={{ fontSize: '0.92rem', fontWeight: 700, margin: '0.4rem 0 0.85rem' }}>
                      Upload Study Material
                    </h5>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
                      Upload notes or documents to create your first subject automatically.
                    </p>
                    <button
                      onClick={() => navigate('/materials')}
                      className="btn btn-primary"
                      style={{ width: '100%', fontSize: '0.88rem', padding: '0.6rem', justifyContent: 'center' }}
                    >
                      <BookOpen size={16} />
                      <span>Upload Material</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </aside>
      </div>
    </DashboardLayout>
  );
}
