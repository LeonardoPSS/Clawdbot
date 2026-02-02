import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Shield, Brain, Activity, MessageSquare,
  Terminal, Cpu, Zap, RefreshCcw, Play,
  Settings, LogOut, Radio, TrendingUp
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const API_HOST = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const API_BASE = `http://${API_HOST}:8001/api`;
const WS_BASE = `ws://${API_HOST}:8001/ws`;

function App() {
  const [identity, setIdentity] = useState('');
  const [tasks, setTasks] = useState('');
  const [moltbook, setMoltbook] = useState(null);
  const [forgeTrends, setForgeTrends] = useState([]);
  const [forgeStatus, setForgeStatus] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [activeView, setActiveView] = useState('chat'); // 'chat' or 'forge'
  const [healthData, setHealthData] = useState([]);
  const [currentHealth, setCurrentHealth] = useState({ cpu: 0, ram: 0 });
  const [wealth, setWealth] = useState({ balance: 0, active_positions: [], history: [] });
  const [wsStatus, setWsStatus] = useState('online');
  const [logs, setLogs] = useState(["[SYSTEM] Nexus Upgrade initialized.", "[CLAWD] Monitoring research channels..."]);

  useEffect(() => {
    // 1. Initial REST Fetch
    const fetchData = () => {
      fetch(`${API_BASE}/identity`).then(r => r.json()).then(data => setIdentity(data?.content || '')).catch(() => { });
      fetch(`${API_BASE}/tasks`).then(r => r.json()).then(data => setTasks(data?.content || '')).catch(() => { });
      fetch(`${API_BASE}/moltbook/activity`).then(r => r.json()).then(data => setMoltbook(data || null)).catch(() => { });
      fetch(`${API_BASE}/forge/trends`).then(r => r.json()).then(data => setForgeTrends(Array.isArray(data) ? data : [])).catch(() => { });
      fetch(`${API_BASE}/forge/status`).then(r => r.json()).then(data => setForgeStatus(data || null)).catch(() => { });
      fetch(`${API_BASE}/wealth`).then(r => r.json()).then(data => setWealth(data || { balance: 0, active_positions: [], history: [] })).catch(() => { });
    };
    fetchData();

    // 2. Health Polling (Periodic Sync)
    const pollHealth = async () => {
      try {
        const resp = await fetch(`${API_BASE}/health`);
        const data = await resp.json();
        const cpu = data.cpu || 1.2;
        const ram = data.ram || 0;
        setCurrentHealth({ cpu, ram });
        setHealthData(prev => [...prev, { time: new Date().toLocaleTimeString(), cpu, ram }].slice(-30));
        setWsStatus('online');
        // Also poll wealth less frequently
        if (Math.random() > 0.7) {
          const wResp = await fetch(`${API_BASE}/wealth`);
          const wData = await wResp.json();
          setWealth(wData);
        }
      } catch (e) {
        setWsStatus('offline');
      }
    };

    pollHealth(); // Initial poll
    const interval = setInterval(pollHealth, 3000);

    return () => clearInterval(interval);
  }, []);

  const runAction = async (action) => {
    addLog(`[ACTION] Triggering ${action}...`);
    try {
      const resp = await fetch(`${API_BASE}/actions/${action}`, { method: 'POST' });
      const result = await resp.json();
      addLog(`[SYSTEM] ${result.status || result.error}`);
    } catch (e) {
      addLog(`[ERROR] Connection failed.`);
    }
  };

  const sendChatMessage = async (e) => {
    if (e) e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { user: userMsg, bot: '...' }]);

    try {
      const resp = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userMsg })
      });
      const result = await resp.json();
      setChatHistory(prev => prev.map((msg, i) => i === prev.length - 1 ? { user: userMsg, bot: result.response } : msg));
    } catch (e) {
      setChatHistory(prev => prev.map((msg, i) => i === prev.length - 1 ? { user: userMsg, bot: "Connection error." } : msg));
    }
  };

  const addLog = (msg) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 15)]);
  };

  return (
    <div className="dashboard-container">
      <div className="neural-grid"></div>

      <header>
        <div className="logo"><Terminal size={24} /> CLAWDBOT NEXUS <span className="status-pulsing" style={{ fontSize: '0.6rem' }}>v3.0 NEXUS</span></div>
        <div style={{ display: 'flex', gap: '30px', fontSize: '0.8rem', fontWeight: 'bold' }}>
          <span>NEURAL SYNC: <span style={{ color: wsStatus === 'online' ? '#00ff88' : '#ff4444' }}>{wsStatus.toUpperCase()}</span></span>
          <button
            onClick={() => window.location.reload()}
            style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.6rem', textDecoration: 'underline', padding: 0 }}
            hidden={wsStatus === 'online'}
          >RELOAD</button>
          <span>GATEWAY: <span className="status-online">ACTIVE</span></span>
          <Radio size={16} className={wsStatus === 'online' ? "status-online status-pulsing" : "status-offline"} />
        </div>
      </header>

      {/* LEFT: MATRIX & CONTROL */}
      <div className="glass-card">
        <h2><Brain size={18} /> Cognitive Matrix</h2>
        <div className="scroll-area markdown-content">
          <ReactMarkdown>{identity}</ReactMarkdown>
        </div>

        <div style={{ marginTop: '25px' }}>
          <h2><Zap size={18} /> Action Center</h2>
          <button className="action-btn" onClick={() => runAction('sync')}>
            <RefreshCcw size={14} /> Force Neural Sync
          </button>
          <button className="action-btn" onClick={() => runAction('moltbook')}>
            <Play size={14} /> Trigger Moltbook Cycle
          </button>
          <button className="action-btn" style={{ borderColor: '#0077b5', color: '#0077b5' }} onClick={() => runAction('linkedin')}>
            <Shield size={14} /> Activate LinkedIn Evolution
          </button>
        </div>
      </div>

      {/* CENTER: MISSION LOG & THE FORGE */}
      <div className="glass-card">
        <div style={{ display: 'flex', gap: '20px', marginBottom: '10px' }}>
          <h2
            style={{
              margin: 0,
              paddingBottom: '5px',
              borderBottom: activeView === 'chat' ? '2px solid var(--accent-primary)' : 'none',
              opacity: activeView === 'chat' ? 1 : 0.4,
              cursor: 'pointer'
            }}
            onClick={() => setActiveView('chat')}
          ><MessageSquare size={18} /> Terminal</h2>
          <h2
            style={{
              margin: 0,
              paddingBottom: '5px',
              borderBottom: activeView === 'forge' ? '2px solid var(--accent-secondary)' : 'none',
              opacity: activeView === 'forge' ? 1 : 0.4,
              cursor: 'pointer'
            }}
            onClick={() => setActiveView('forge')}
          ><Zap size={18} /> The Forge</h2>
        </div>

        <div className="scroll-area">
          {activeView === 'chat' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '10px' }}>
              {chatHistory.map((chat, i) => (
                <div key={i}>
                  <div style={{ color: 'var(--accent-primary)', fontSize: '0.7rem', fontWeight: 'bold', marginBottom: '4px' }}>LEONARDO:</div>
                  <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '8px', fontSize: '0.85rem' }}>{chat.user}</div>
                  <div style={{ color: 'var(--accent-secondary)', fontSize: '0.7rem', fontWeight: 'bold', marginTop: '10px', marginBottom: '4px', textAlign: 'right' }}>CLAWDBOT:</div>
                  <div style={{
                    background: 'rgba(255, 0, 234, 0.15)',
                    padding: '14px',
                    borderRadius: '12px 12px 0 12px',
                    fontSize: '0.95rem',
                    textAlign: 'left',
                    border: '1px solid rgba(255, 0, 234, 0.4)',
                    color: '#ffffff',
                    fontWeight: '500',
                    boxShadow: '0 4px 15px rgba(255, 0, 234, 0.1)',
                    width: 'fit-content',
                    maxWidth: '90%',
                    marginLeft: 'auto'
                  }}>
                    {chat.bot}
                  </div>
                </div>
              ))}
              {chatHistory.length === 0 && (
                <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: '0.8rem', fontStyle: 'italic' }}>
                  Establish connection with Clawdbot to begin...
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: '10px' }}>
              <div style={{ marginBottom: '25px' }}>
                <h2 style={{ color: 'var(--accent-secondary)', fontSize: '0.9rem' }}><Activity size={18} /> Market Incubator Status</h2>
                {forgeStatus ? (
                  <div style={{ background: 'rgba(255, 0, 234, 0.05)', padding: '15px', borderRadius: '12px', border: '1px solid rgba(255, 0, 234, 0.1)', marginTop: '10px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ACTIVE INCUBATION:</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent-secondary)' }}>{forgeStatus.current_project}</div>
                    <div style={{ fontSize: '0.8rem', marginTop: '5px' }}>PHASE: <span className="status-online">{forgeStatus.status}</span></div>
                    <div style={{ fontSize: '0.6rem', marginTop: '10px', opacity: 0.5, fontFamily: 'monospace' }}>{forgeStatus.path}</div>
                  </div>
                ) : <div style={{ opacity: 0.5 }}>Forge is currently idle.</div>}
              </div>

              <h2 style={{ fontSize: '0.9rem', marginBottom: '15px' }}><Shield size={18} /> Mission Protocols</h2>
              <div className="markdown-content">
                <ReactMarkdown>{tasks}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>

        {activeView === 'chat' && (
          <form onSubmit={sendChatMessage} style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
            <input
              type="text"
              className="action-btn"
              style={{ textAlign: 'left', textTransform: 'none', background: 'rgba(0,0,0,0.3)', flexGrow: 1, margin: 0 }}
              placeholder="Interacting with neural context..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
            />
            <button onClick={() => runAction('trade')} className="action-btn" style={{ borderColor: 'var(--accent-secondary)', color: 'var(--accent-secondary)' }}>
              <TrendingUp size={16} /> TRIGGER TRADE CYCLE
            </button>
            <button onClick={() => runAction('forge')} className="action-btn" style={{ background: 'linear-gradient(45deg, #ff00ea, #00f2ff)', color: '#000', border: 'none' }}>
              <Zap size={16} /> IGNITION: START THE FORGE
            </button>
          </form>
        )}
      </div>

      {/* RIGHT: HEALTH & LOGS */}
      <div className="glass-card">
        <h2><Activity size={18} /> Biometric Stream (CPU)</h2>
        <div style={{ height: '180px', width: '100%', minHeight: '180px' }}>
          {wsStatus === 'online' && healthData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={healthData}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2ff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00f2ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="cpu" stroke="#00f2ff" fillOpacity={1} fill="url(#colorCpu)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-dim)', fontSize: '0.7rem', border: '1px dashed var(--glass-border)' }}>
              <div>{wsStatus === 'online' ? 'INITIALIZING NEURAL BROADCAST...' : 'OFFLINE: WAITING FOR SYNC...'}</div>
              {wsStatus !== 'online' && <button onClick={() => window.location.reload()} className="action-btn" style={{ fontSize: '0.6rem', padding: '5px 10px', marginTop: '10px' }}>RETRY SYNC</button>}
            </div>
          )}
        </div>

        <div style={{ marginTop: '20px', flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          <h2><Radio size={18} /> Neural Feed (Logs)</h2>
          <div className="scroll-area" style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', fontFamily: 'monospace', fontSize: '0.7rem' }}>
            {Array.isArray(logs) && logs.map((log, i) => (
              <div key={i} style={{ marginBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '2px' }}>
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* BOTTOM: ANALYTICS PREVIEW */}
      <div className="bottom-modules">
        <div className="glass-card" style={{ flexDirection: 'row', alignItems: 'center', gap: '15px' }}>
          <Cpu className="status-online" size={32} />
          <div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{currentHealth.cpu}%</div>
            <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)' }}>CPU NEURAL LOAD</div>
          </div>
        </div>
        <div className="glass-card">
          <h2><Activity size={18} /> Memory Buffer</h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--accent-secondary)' }}>{currentHealth.ram.toFixed(1)}%</div>
          </div>
        </div>

        <div className="glass-card" style={{ border: '1px solid var(--accent-secondary)', boxShadow: '0 0 15px rgba(255, 0, 234, 0.2)' }}>
          <h2><TrendingUp size={18} /> Neural Wealth</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '900', color: '#fff' }}>${(wealth?.balance || 0).toLocaleString()}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ACTIVE POSITIONS: {(wealth?.active_positions || []).length}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '10px' }}>
              {Array.isArray(wealth.active_positions) && wealth.active_positions.slice(0, 3).map((pos, i) => (
                <div key={i} style={{ fontSize: '0.6rem', padding: '3px 6px', background: 'rgba(0,255,136,0.1)', border: '1px solid #00ff88', borderRadius: '4px', color: '#00ff88' }}>
                  {(pos.title || 'Position').substring(0, 10)}... (+{(pos.roi || 0).toFixed(1)}%)
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="glass-card" style={{ flexDirection: 'row', alignItems: 'center', gap: '15px' }}>
          <MessageSquare className="status-online" size={32} />
          <div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{moltbook?.agent?.name || "Clawdbot"}</div>
            <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)' }}>MOLTBOOK STATUS: ACTIVE</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
