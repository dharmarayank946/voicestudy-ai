import React from 'react';
import { 
  Home, 
  BookOpen, 
  Brain, 
  HelpCircle, 
  BarChart3, 
  Settings, 
  Sparkles,
  Radio
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, healthData }) {
  const navItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'study', label: 'Study', icon: BookOpen },
    { id: 'memory', label: 'Memory', icon: Brain },
    { id: 'quiz', label: 'Quiz', icon: HelpCircle },
    { id: 'progress', label: 'Progress', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const qdrantConnected = healthData?.vector_memory?.status === 'connected';
  const totalMemories = healthData?.vector_memory?.total_memories || 0;

  return (
    <aside style={{
      width: '260px',
      height: '100vh',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem 1rem',
      flexShrink: 0
    }}>
      {/* Brand Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0 0.5rem 1.5rem 0.5rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'var(--gradient-cyan-emerald)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(0, 242, 254, 0.4)'
        }}>
          <Sparkles size={20} color="#040911" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
            VoiceStudy <span style={{ color: 'var(--accent-cyan)' }}>AI</span>
          </h1>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '500' }}>
            Speak. Remember. Revise.
          </p>
        </div>
      </div>

      {/* Navigation items */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.85rem',
                padding: '0.75rem 1rem',
                borderRadius: '12px',
                border: 'none',
                background: isActive ? 'rgba(0, 242, 254, 0.1)' : 'transparent',
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                fontWeight: isActive ? '600' : '500',
                fontSize: '0.92rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <Icon size={19} color={isActive ? 'var(--accent-cyan)' : 'var(--text-muted)'} />
              <span>{item.label}</span>
              {item.id === 'memory' && totalMemories > 0 && (
                <span className="badge badge-emerald" style={{ marginLeft: 'auto', padding: '0.15rem 0.5rem', fontSize: '0.7rem' }}>
                  {totalMemories}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Integration Badges */}
      <div style={{
        marginTop: 'auto',
        background: 'rgba(10, 16, 26, 0.7)',
        borderRadius: '14px',
        padding: '1rem',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.6rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
          <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Brain size={14} color="var(--accent-cyan)" /> Qdrant Vector
          </span>
          <span style={{ color: qdrantConnected ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontWeight: '600' }}>
            ● {qdrantConnected ? 'Active' : 'Offline'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
          <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Radio size={14} color="var(--accent-emerald)" /> Omi Voice
          </span>
          <span className="badge badge-cyan" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
            Ready
          </span>
        </div>
      </div>
    </aside>
  );
}
