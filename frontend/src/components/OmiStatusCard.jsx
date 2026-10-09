import React, { useState, useEffect } from 'react';
import { Radio, RefreshCw, Terminal, CheckCircle2, Play, Code, AlertTriangle } from 'lucide-react';

export default function OmiStatusCard() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [testStatus, setTestStatus] = useState(null);
  const [showLogModal, setShowLogModal] = useState(false);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/omi/logs');
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (err) {
      console.warn("Failed to fetch Omi logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulateWebhook = async () => {
    try {
      setTestStatus("Sending test Omi payload...");
      const res = await fetch('/api/omi/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json();
        setTestStatus(`Success! Simulated webhook queued for UID: ${data.uid}`);
        fetchLogs();
      } else {
        setTestStatus("Failed to send test webhook");
      }
    } catch (err) {
      setTestStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div className="glass-card" style={{ borderColor: 'rgba(0, 242, 254, 0.2)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Radio size={20} color="var(--accent-cyan)" />
          <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            Omi Hardware Webhook Endpoint
          </h4>
        </div>
        <span className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <CheckCircle2 size={12} /> FastAPI Webhook Ready
        </span>
      </div>

      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.85rem' }}>
        Configure these HTTPS URLs in your <strong>Omi Mobile App</strong> (Developer Mode):
      </p>

      {/* Webhook URLs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1rem' }}>
        <div style={{ padding: '0.5rem 0.75rem', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--accent-cyan)' }}>
          POST <strong>/omi/conversation?uid=YOUR_UID</strong>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--accent-purple)' }}>
          POST <strong>/omi/realtime?uid=YOUR_UID</strong>
        </div>
      </div>

      {/* Webhook Log Stats & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
        <div>
          Received Logs: <strong style={{ color: 'var(--text-primary)' }}>{logs.length}</strong>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            className="btn-secondary" 
            onClick={handleSimulateWebhook}
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
          >
            <Play size={12} color="var(--accent-emerald)" /> Test Webhook
          </button>
          <button 
            className="btn-secondary" 
            onClick={() => setShowLogModal(!showLogModal)}
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
          >
            <Terminal size={12} color="var(--accent-cyan)" /> Inspect Logs
          </button>
        </div>
      </div>

      {testStatus && (
        <div style={{ marginTop: '0.75rem', fontSize: '0.78rem', color: 'var(--accent-cyan)', background: 'rgba(0, 242, 254, 0.1)', padding: '0.4rem 0.75rem', borderRadius: '6px' }}>
          {testStatus}
        </div>
      )}

      {/* Inspection Modal / Drawer */}
      {showLogModal && (
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          background: 'rgba(8, 12, 20, 0.95)',
          borderRadius: '10px',
          border: '1px solid var(--border-subtle)',
          maxHeight: '260px',
          overflowY: 'auto'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h5 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: '700' }}>Recent Omi Webhook Payload Logs (Sanitized)</h5>
            <button className="btn-secondary" onClick={fetchLogs} style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}>
              <RefreshCw size={10} /> Refresh
            </button>
          </div>

          {logs.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No Omi webhook payloads received yet. Trigger test or speak with Omi hardware!</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {logs.map((log) => (
                <div key={log.id} style={{ background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '6px', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                    <span>[{log.event_type}] UID: {log.uid}</span>
                    <span>{new Date(log.received_at).toLocaleTimeString()}</span>
                  </div>
                  <pre style={{ margin: '0.25rem 0 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: 'var(--text-secondary)' }}>
                    {JSON.stringify(log.sanitized_payload, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
