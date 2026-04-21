import { useState, useEffect, useRef } from 'react';
import {
  Plus, LogOut,
  Menu, X, ChevronRight,
  Clipboard, ArrowUp,
  Eye, EyeOff, CheckSquare, Square,
  Download, FileText, FileJson,
  Trash2, Pencil
} from 'lucide-react';
import axios from 'axios';
import { jsPDF } from 'jspdf';

const getTimestamp = () => {
  const d = new Date();
  return d.getFullYear().toString() +
    String(d.getMonth() + 1).padStart(2, '0') +
    String(d.getDate()).padStart(2, '0') + '_' +
    String(d.getHours()).padStart(2, '0') +
    String(d.getMinutes()).padStart(2, '0') +
    String(d.getSeconds()).padStart(2, '0');
};

// Strip emojis and clean heading text
const cleanLine = (line: string) => {
  return line
    .replace(/[\u{1F300}-\u{1FAD6}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu, '')
    .replace(/[*#]+/g, '')
    .trim();
};

// Map emoji headers to clean readable labels
const HEADER_MAP: Record<string, string> = {
  'what you shared': 'SYMPTOMS SHARED',
  'possible causes': 'POSSIBLE CAUSES',
  'ranked': 'POSSIBLE CAUSES',
  'recommended medicines': 'RECOMMENDED MEDICINES',
  'care': 'RECOMMENDED MEDICINES',
  'when to seek medical help': 'WHEN TO SEE A DOCTOR',
  'wellness tips': 'WELLNESS TIPS',
  'ai confidence': 'AI CONFIDENCE SCORE',
  'observed visual findings': 'VISUAL FINDINGS',
  'possible interpretations': 'POSSIBLE INTERPRETATIONS',
  'clinical recommendation': 'CLINICAL RECOMMENDATION',
  'image type': 'IMAGE TYPE',
};

const getCleanHeader = (rawLine: string): string | null => {
  const cleaned = cleanLine(rawLine).toLowerCase();
  for (const [key, label] of Object.entries(HEADER_MAP)) {
    if (cleaned.includes(key)) return label;
  }
  // If line starts with emoji and has text, treat as a header
  if (/^[\u{1F300}-\u{1FAD6}\u{2600}-\u{27BF}]/u.test(rawLine)) {
    return cleanLine(rawLine).toUpperCase();
  }
  return null;
};

const parseReport = (text: string) => {
  const sections: Record<string, string> = {};
  const lines = text.split('\n');
  let currentKey = '';
  for (const line of lines) {
    const header = getCleanHeader(line);
    if (header) {
      currentKey = header;
      sections[currentKey] = '';
    } else if (currentKey) {
      const cleaned = cleanLine(line);
      if (cleaned) {
        sections[currentKey] += (sections[currentKey] ? '\n' : '') + cleaned;
      }
    }
  }
  return sections;
};

const promptPatientInfo = (): { name: string; age: string } | null => {
  const name = prompt('Enter patient name (optional):');
  if (name === null) return null; // User cancelled
  const age = prompt('Enter patient age (optional):');
  if (age === null) return null;
  return { name: name.trim() || 'Not provided', age: age.trim() || 'Not provided' };
};

const downloadAsPDF = (text: string, userQuery?: string) => {
  const patient = promptPatientInfo();
  if (!patient) return;
  try {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 15;
    const usable = pageWidth - margin * 2;
    let y = 20;
    const lineH = 6;
    const now = new Date();
    const dateStr = now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });

    const addText = (txt: string, size = 10, bold = false, color: [number, number, number] = [0, 0, 0]) => {
      doc.setTextColor(...color);
      doc.setFontSize(size);
      doc.setFont('helvetica', bold ? 'bold' : 'normal');
      const lines = doc.splitTextToSize(txt, usable);
      for (const l of lines) {
        if (y > 275) { doc.addPage(); y = 20; }
        doc.text(l, margin, y);
        y += lineH;
      }
    };

    const addSection = (title: string) => {
      y += 3;
      if (y > 270) { doc.addPage(); y = 20; }
      doc.setDrawColor(20, 184, 166);
      doc.setLineWidth(0.5);
      doc.line(margin, y, margin + 40, y);
      y += 5;
      addText(title, 11, true, [20, 120, 110]);
      y += 1;
    };

    // === HEADER BAR ===
    doc.setFillColor(20, 184, 166);
    doc.rect(0, 0, pageWidth, 16, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(15);
    doc.setFont('helvetica', 'bold');
    doc.text('WELLORA - AI Health Report', margin, 11);
    doc.setTextColor(0, 0, 0);
    y = 24;

    // === PATIENT INFO ===
    addText(`Report Date: ${dateStr}`, 9);
    addText(`Patient Name: ${patient.name}`, 10, true);
    addText(`Patient Age: ${patient.age}`, 10, true);
    if (userQuery) { addText(`Chief Complaint: ${userQuery}`, 10); }
    y += 4;

    // === REPORT BODY (clean headings) ===
    const contentLines = text.split('\n');
    for (const line of contentLines) {
      const header = getCleanHeader(line);
      if (header) {
        addSection(header);
      } else {
        const cleaned = cleanLine(line);
        if (cleaned) {
          addText(cleaned, 10, false);
        }
      }
    }

    // === FOOTER ===
    y += 8;
    if (y > 270) { doc.addPage(); y = 20; }
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, y, pageWidth - margin, y);
    y += 5;
    addText('Disclaimer: This report is AI-generated for educational purposes only. It does not replace professional medical advice. Always consult a qualified physician.', 8, false, [120, 120, 120]);

    doc.save(`Wellora_Report_${getTimestamp()}.pdf`);
  } catch {
    alert('Unable to generate report at the moment. Please try again.');
  }
};

const downloadAsTXT = (text: string, userQuery?: string) => {
  const patient = promptPatientInfo();
  if (!patient) return;
  try {
    const now = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
    const sections = parseReport(text);
    let content = '========================================\n';
    content += '       WELLORA - AI Health Report\n';
    content += '========================================\n\n';
    content += `Report Date   : ${now}\n`;
    content += `Patient Name  : ${patient.name}\n`;
    content += `Patient Age   : ${patient.age}\n`;
    if (userQuery) content += `Chief Complaint: ${userQuery}\n`;
    content += '\n' + '-'.repeat(40) + '\n\n';
    for (const [heading, body] of Object.entries(sections)) {
      content += `[ ${heading} ]\n`;
      content += body + '\n\n';
    }
    content += '-'.repeat(40) + '\n';
    content += 'Disclaimer: This report is AI-generated for educational purposes only.\nIt does not replace professional medical advice.\n';
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `Wellora_Report_${getTimestamp()}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch {
    alert('Unable to generate report at the moment. Please try again.');
  }
};

const downloadAsJSON = (text: string, userQuery?: string) => {
  const patient = promptPatientInfo();
  if (!patient) return;
  try {
    const sections = parseReport(text);
    const report = {
      title: 'Wellora AI Health Report',
      generated: new Date().toISOString(),
      patient: { name: patient.name, age: patient.age },
      chief_complaint: userQuery || 'N/A',
      report_sections: sections,
      disclaimer: 'This report is AI-generated for educational purposes only. It does not replace professional medical advice.'
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `Wellora_Report_${getTimestamp()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch {
    alert('Unable to generate report at the moment. Please try again.');
  }
};



interface GlmModelResult { model: string; predictions: { label: string; confidence: number; }[]; status: string; error?: string; }
interface GlmAnalysis { caption?: string; summary: string; model?: string; status?: string; model_results?: GlmModelResult[]; }
interface Message {
  id: string; role: 'user' | 'bot'; text: string; timestamp: Date; image?: string; userQuery?: string; glmAnalysis?: GlmAnalysis;
}
interface ChatSession { id: string; title: string; date?: string; }

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const uid = () => Math.random().toString(36).substring(2, 9);

export default function App() {
  const [view, setView] = useState<'landing' | 'auth' | 'chat'>('landing');
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [agreedTerms, setAgreedTerms] = useState(false);
  const [authError, setAuthError] = useState('');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string>(() => localStorage.getItem('wellora_lang') || 'English');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState(uid());
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    localStorage.setItem('wellora_lang', selectedLanguage);
  }, [selectedLanguage]);

  // --- Session Management ---
  const fetchSessions = async () => {
    if (!loggedIn || !email) return;
    try {
      const res = await axios.get(`${API}/sessions`, { params: { user_email: email } });
      setSessions(res.data);
    } catch { /* silent */ }
  };

  const loadSession = async (sessionId: string) => {
    setActiveSession(sessionId);
    try {
      const res = await axios.get(`${API}/history/${sessionId}`);
      const history: Message[] = res.data.history.map((m: any, i: number) => ({
        id: uid() + i,
        role: m.role === 'assistant' ? 'bot' : 'user',
        text: m.content,
        timestamp: new Date(),
      }));
      setMessages(history);
    } catch {
      setMessages([]);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await axios.delete(`${API}/sessions/${sessionId}`);
      if (activeSession === sessionId) {
        setMessages([]);
        setActiveSession(uid());
      }
      fetchSessions();
    } catch { /* silent */ }
  };

  const renameSession = async (sessionId: string, newTitle: string) => {
    if (!newTitle.trim()) return;
    try {
      await axios.patch(`${API}/sessions/${sessionId}`, null, { params: { title: newTitle.trim() } });
      fetchSessions();
    } catch { /* silent */ }
    setEditingSessionId(null);
  };

  const send = async () => {
    if (!input.trim() && !imageFile) return;
    const txt = input;
    const img = imagePreview;
    const file = imageFile;
    setMessages(p => [...p, { id: uid(), role: 'user', text: txt, timestamp: new Date(), image: img || undefined }]);
    setInput('');
    setImagePreview(null);
    setImageFile(null);
    setLoading(true);

    try {
      // ── IMAGE PATH: call /analyze with FormData ──────────────────────────
      if (file) {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(`${API}/analyze`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();

        if (data.error) {
          setMessages(p => [...p, { id: uid(), role: 'bot', text: `⚠️ ${data.error}`, timestamp: new Date() }]);
        } else {
          const analysisText = data.analysis || 'Analysis complete.';
          setMessages(p => [...p, {
            id: uid(),
            role: 'bot',
            text: analysisText,
            timestamp: new Date(),
            userQuery: txt || '(image attached)',
            glmAnalysis: { summary: analysisText, caption: 'Image analyzed successfully.', status: 'success' }
          }]);
        }

        // Also send text part to /chat if user typed something
        if (txt.trim()) {
          const r = await axios.post(`${API}/chat`, {
            session_id: activeSession,
            message: txt,
            is_logged_in: loggedIn,
            user_email: email,
            language: selectedLanguage,
            image: null
          });
          setMessages(p => [...p, { id: uid(), role: 'bot', text: r.data.response, timestamp: new Date(), userQuery: txt }]);
        }

      // ── TEXT ONLY PATH: call /chat as before ─────────────────────────────
      } else {
        const r = await axios.post(`${API}/chat`, {
          session_id: activeSession,
          message: txt || '(image attached)',
          is_logged_in: loggedIn,
          user_email: email,
          language: selectedLanguage,
          image: img || null
        });
        setMessages(p => [...p, { id: uid(), role: 'bot', text: r.data.response, timestamp: new Date(), userQuery: txt || '(image attached)', glmAnalysis: r.data.glm_analysis || undefined }]);
      }

      fetchSessions();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'I am having trouble connecting to my medical intelligence core. Please ensure the backend server is running and try again.';
      setMessages(p => [...p, { id: uid(), role: 'bot', text: errorMsg, timestamp: new Date() }]);
    } finally { setLoading(false); }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Production hardening: Limit images to 3MB
    if (file.size > 3 * 1024 * 1024) {
      alert("Image is too large (max 3 MB). Please upload a smaller image.");
      e.target.value = '';
      return;
    }

    setImageFile(file);
    const reader = new FileReader();
    reader.onload = () => setImagePreview(reader.result as string);
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const newChat = () => { setMessages([]); setActiveSession(uid()); };

  const enterChat = () => {
    setView('chat');
    setMessages([]);
  };

  const handleLogin = async () => {
    setAuthError('');
    if (!email.trim() || !password.trim()) { setAuthError('Please fill in all fields.'); return; }
    try {
      await axios.post(`${API}/auth/login`, { email, password });
      setLoggedIn(true); enterChat();
      // Fetch sessions after login
      setTimeout(async () => {
        try {
          const res = await axios.get(`${API}/sessions`, { params: { user_email: email } });
          setSessions(res.data);
        } catch { /* silent */ }
      }, 100);
    } catch (e: any) {
      setAuthError(e?.response?.status === 401 ? 'Invalid email or password.' : 'Login failed. Check your connection.');
    }
  };

  const handleSignup = async () => {
    setAuthError('');
    if (!fullName.trim() || !email.trim() || !password.trim()) { setAuthError('Please fill in all fields.'); return; }
    if (password !== confirmPass) { setAuthError('Passwords do not match.'); return; }
    if (!agreedTerms) { setAuthError('Please agree to the terms.'); return; }
    try {
      await axios.post(`${API}/auth/signup`, { email, password });
      setLoggedIn(true); enterChat();
    } catch (e: any) {
      setAuthError(e?.response?.status === 400 ? 'Account already exists.' : 'Signup failed. Check your connection.');
    }
  };

  const useSuggestion = (text: string) => {
    setInput(text);
  };

  // ======== LANDING ========
  if (view === 'landing') return (
    <div className="landing-page">
      <div className="landing-logo"><img src="/wellora-logo.png" alt="Wellora Logo" style={{ width: '120px', height: '120px', objectFit: 'contain', borderRadius: '8px' }} /></div>
      <h1>Wellora</h1>
      <div className="landing-actions" style={{ marginTop: '32px' }}>
        <button className="landing-start-btn" onClick={() => { setAuthMode('signup'); setView('auth'); }}>
          Get Started <ChevronRight size={20} />
        </button>
        <button className="landing-signin-btn" onClick={() => { setAuthMode('login'); setView('auth'); }}>
          Sign In
        </button>
      </div>
      <div className="landing-footer">For educational purposes only. Not medical advice.</div>
    </div>
  );

  // ======== AUTH ========
  if (view === 'auth') return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-image"><img src="/wellora-logo.png" alt="Wellora Logo" style={{ width: '60px', height: '60px', objectFit: 'contain', borderRadius: '6px' }} /></div>
        </div>
        <h2>{authMode === 'login' ? 'Welcome back' : 'Create account'}</h2>
        <p className="auth-subtitle">{authMode === 'login' ? 'Sign in to Wellora' : 'Get started for free'}</p>

        {authError && <div className="auth-error">{authError}</div>}

        {authMode === 'signup' && (
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input className="form-input" type="text" placeholder="John Doe" value={fullName} onChange={e => setFullName(e.target.value)} />
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Email</label>
          <input className="form-input" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <div style={{ position: 'relative' }}>
            <input className="form-input" type={showPass ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} />
            <button className="pass-toggle" onClick={() => setShowPass(!showPass)}>
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {authMode === 'signup' && (
          <>
            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input className="form-input" type="password" placeholder="••••••••" value={confirmPass} onChange={e => setConfirmPass(e.target.value)} />
            </div>
            <div className="auth-terms" onClick={() => setAgreedTerms(!agreedTerms)}>
              {agreedTerms ? <CheckSquare size={18} style={{ color: 'var(--accent)' }} /> : <Square size={18} color="var(--text3)" />}
              <span>I agree to the Terms and Privacy Policy</span>
            </div>
          </>
        )}

        <button className="auth-submit-btn" onClick={authMode === 'login' ? handleLogin : handleSignup}>
          {authMode === 'login' ? 'Continue' : 'Create Account'}
        </button>

        <div className="auth-link">
          {authMode === 'login' ? (
            <>Don't have an account? <button onClick={() => { setAuthMode('signup'); setAuthError(''); }}>Sign up</button></>
          ) : (
            <>Already have an account? <button onClick={() => { setAuthMode('login'); setAuthError(''); }}>Sign in</button></>
          )}
        </div>
        <button className="auth-back" onClick={() => setView('landing')}>← Back</button>
      </div>
    </div>
  );

  // ======== CHAT ========
  return (
    <div className="app-layout">
      {/* Sidebar */}
      <nav className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
        <div className="sidebar-top">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', padding: '0 4px' }}>
            <img src="/wellora-logo.png" alt="Wellora" style={{ width: '40px', height: '40px', borderRadius: '6px', objectFit: 'contain' }} />
            <span style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--text)' }}>Wellora</span>
          </div>
          <button className="new-chat-btn" onClick={newChat}>
            <Plus size={18} /> New chat
          </button>
        </div>

        <div className="sidebar-list">
          <div className="sidebar-section-label">Your Chats</div>
          {sessions.length === 0 && (
            <div className="sidebar-empty">No conversations yet</div>
          )}
          {sessions.map(s => (
            <div
              key={s.id}
              className={`sidebar-item ${activeSession === s.id ? 'active' : ''}`}
              onClick={() => loadSession(s.id)}
            >
              {editingSessionId === s.id ? (
                <input
                  className="sidebar-rename-input"
                  value={editingTitle}
                  onChange={e => setEditingTitle(e.target.value)}
                  onBlur={() => renameSession(s.id, editingTitle)}
                  onKeyDown={e => { if (e.key === 'Enter') renameSession(s.id, editingTitle); if (e.key === 'Escape') setEditingSessionId(null); }}
                  onClick={e => e.stopPropagation()}
                  autoFocus
                />
              ) : (
                <>
                  <span className="sidebar-item-title">{s.title}</span>
                  <div className="sidebar-item-actions">
                    <button
                      className="sidebar-action-btn"
                      onClick={e => { e.stopPropagation(); setEditingSessionId(s.id); setEditingTitle(s.title); }}
                      title="Rename"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      className="sidebar-action-btn sidebar-delete-btn"
                      onClick={e => { e.stopPropagation(); deleteSession(s.id); }}
                      title="Delete"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">
              {loggedIn ? (email[0]?.toUpperCase() || 'U') : 'G'}
            </div>
            <span className="sidebar-user-name">
              {loggedIn ? email.split('@')[0] : 'Guest'}
            </span>
            <button className="sidebar-logout-btn" onClick={() => { setLoggedIn(false); setMessages([]); setSessions([]); setView('landing'); }}>
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </nav>

      {/* Toggle */}
      <button className={`sidebar-toggle-btn ${sidebarOpen ? 'shifted' : ''}`} onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
      </button>

      {/* Main */}
      <div className="main-area">
        <div className="chat-header">
          <div className="language-selector">
            <button
              className={`lang-btn ${selectedLanguage === 'English' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('English')}
            >
              🇬🇧 English
            </button>
            <button
              className={`lang-btn ${selectedLanguage === 'Hindi' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('Hindi')}
            >
              🇮🇳 Hindi
            </button>
            <button
              className={`lang-btn ${selectedLanguage === 'Telugu' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('Telugu')}
            >
              🇮🇳 Telugu
            </button>
          </div>
        </div>
        <div className="chat-scroll">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-logo"><img src="/wellora-logo.png" alt="Wellora Logo" style={{ width: '80px', height: '80px', objectFit: 'contain', borderRadius: '8px' }} /></div>
              <h2>How can I help you today?</h2>
              <div className="welcome-suggestions">
                <div className="suggestion-card" onClick={() => useSuggestion('I have a headache and mild fever since yesterday')}>
                  <strong>Symptom check</strong>
                  I have a headache and mild fever
                </div>
                <div className="suggestion-card" onClick={() => useSuggestion('What are some home remedies for a sore throat?')}>
                  <strong>Home remedies</strong>
                  Sore throat relief options
                </div>
                <div className="suggestion-card" onClick={() => useSuggestion('My child has been coughing for 3 days, should I worry?')}>
                  <strong>Child health</strong>
                  Persistent cough in children
                </div>
                <div className="suggestion-card" onClick={() => useSuggestion('What does high blood pressure mean?')}>
                  <strong>Health info</strong>
                  Understanding blood pressure
                </div>
              </div>
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map(m => (
                <div key={m.id} className={`msg-row ${m.role}`}>
                  {m.role === 'bot' ? (
                    <div className="bot-msg">
                      <div className="bot-msg-avatar"><img src="/wellora-logo.png" alt="Wellora" style={{ width: '100%', height: '100%', objectFit: 'contain', borderRadius: '50%' }} /></div>
                      <div className="bot-msg-body">
                        {/* GLM-4V Image Analysis Card */}
                        {m.glmAnalysis && (
                          <div className="glm-analysis-card">
                            <div className="glm-card-header">
                              <span className="glm-card-icon">🔬</span>
                              <span className="glm-card-title">GLM-4V Image Analysis</span>
                            </div>
                            <div 
                              className="glm-card-summary" 
                              dangerouslySetInnerHTML={{ 
                                __html: (m.glmAnalysis.summary || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
                              }} 
                            />

                            {m.glmAnalysis.caption && (
                              <div className="glm-caption-box">
                                <div className="glm-caption-label">Visual Summary:</div>
                                <div className="glm-caption-text">{m.glmAnalysis.caption}</div>
                              </div>
                            )}

                            {m.glmAnalysis.model_results && m.glmAnalysis.model_results.length > 0 && (
                              <div className="glm-models-grid">
                                {m.glmAnalysis.model_results.map((mr, mi) => (
                                  mr.status === 'success' && mr.predictions.length > 0 && (
                                    <div key={mi} className="glm-model-block">
                                      <div className="glm-model-name">{mr.model}</div>
                                      {mr.predictions.slice(0, 3).map((p, pi) => (
                                        <div key={pi} className="glm-prediction-row">
                                          <div className="glm-pred-label">{p.label}</div>
                                          <div className="glm-pred-bar-track">
                                            <div
                                              className="glm-pred-bar-fill"
                                              style={{ width: `${Math.min(p.confidence, 100)}%` }}
                                            />
                                          </div>
                                          <div className="glm-pred-conf">{p.confidence}%</div>
                                        </div>
                                      ))}
                                    </div>
                                  )
                                ))}
                              </div>
                            )}
                            <div className="glm-card-disclaimer">AI-assisted analysis — not a clinical diagnosis.</div>
                          </div>
                        )}
                        <div className="bot-msg-text">{m.text}</div>
                        {m.image && <img src={m.image} alt="Attached" className="msg-image" />}
                        <div className="bot-msg-actions">
                          <button onClick={() => navigator.clipboard.writeText(m.text)} title="Copy"><Clipboard size={14} /></button>
                          <button onClick={() => downloadAsPDF(m.text, m.userQuery)} title="Download PDF" className="download-btn"><Download size={14} /></button>
                          <button onClick={() => downloadAsTXT(m.text, m.userQuery)} title="Download TXT" className="download-btn"><FileText size={14} /></button>
                          <button onClick={() => downloadAsJSON(m.text, m.userQuery)} title="Download JSON" className="download-btn"><FileJson size={14} /></button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="user-msg">
                      <div className="user-msg-bubble">
                        {m.image && <img src={m.image} alt="Attached" className="msg-image" />}
                        {m.text && <span>{m.text}</span>}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-wrapper">
            <div className="input-box">
              <input type="file" accept="image/*" ref={fileInputRef} onChange={handleImageSelect} style={{ display: 'none' }} />
              <button className="attach-btn" onClick={() => fileInputRef.current?.click()} title="Attach image">
                <Plus size={20} />
              </button>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column' as const }}>
                {imagePreview && (
                  <div className="image-preview">
                    <img src={imagePreview} alt="Preview" />
                    <button className="image-preview-remove" onClick={() => { setImagePreview(null); setImageFile(null); }}>✕</button>
                  </div>
                )}
                <textarea
                  className="input-field"
                  rows={1}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                  placeholder="Message Wellora..."
                />
              </div>
              <button className={`send-btn ${(input.trim() || imageFile) ? 'active' : 'inactive'}`} onClick={send}>
                <ArrowUp size={18} />
              </button>
            </div>
            <div className="input-disclaimer">Wellora can make mistakes. Not a substitute for professional medical advice.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
