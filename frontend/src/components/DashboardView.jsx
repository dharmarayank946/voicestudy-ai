import React from 'react';
import { Brain, BookOpen, HelpCircle, Sparkles, Clock, ArrowRight, CheckCircle2 } from 'lucide-react';
import VoiceOrb from './VoiceOrb';

export default function DashboardView({ memories, stats, onProcessInput, isProcessing, responseData, setActiveTab }) {
  const recentMemories = memories.slice(0, 4);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Voice Orb Main Interface */}
      <div className="glass-card" style={{ background: 'linear-gradient(180deg, rgba(13, 18, 29, 0.8) 0%, rgba(7, 10, 15, 0.9) 100%)' }}>
        <VoiceOrb 
          onProcessInput={onProcessInput}
          isProcessing={isProcessing}
          responseData={responseData}
        />
      </div>

      {/* Stats Counters Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>Total Memories</span>
            <div style={{ padding: '0.5rem', borderRadius: '10px', background: 'rgba(0, 242, 254, 0.1)' }}>
              <Brain size={20} color="var(--accent-cyan)" />
            </div>
          </div>
          <h3 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            {stats.total_memories || memories.length || 0}
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--accent-emerald)', marginTop: '0.25rem' }}>
            ✓ Qdrant Vector Store
          </p>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>Topics Studied</span>
            <div style={{ padding: '0.5rem', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.1)' }}>
              <BookOpen size={20} color="var(--accent-emerald)" />
            </div>
          </div>
          <h3 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            {stats.total_topics || 3}
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            DBMS, Computer Networks, OS
          </p>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>Revision Quizzes</span>
            <div style={{ padding: '0.5rem', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.1)' }}>
              <HelpCircle size={20} color="var(--accent-purple)" />
            </div>
          </div>
          <h3 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            5
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--accent-purple)', marginTop: '0.25rem' }}>
            Active Recall Mode
          </p>
        </div>
      </div>

      {/* Recent Study Activity Timeline */}
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              Recent Study Memories
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Semantic vectors stored in Qdrant database
            </p>
          </div>
          <button 
            className="btn-secondary"
            onClick={() => setActiveTab('memory')}
            style={{ fontSize: '0.82rem', padding: '0.45rem 0.85rem' }}
          >
            View All Memories <ArrowRight size={14} />
          </button>
        </div>

        {recentMemories.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '1rem 0' }}>
            No study memories saved yet. Speak to the orb above to create your first study note!
          </p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            {recentMemories.map((m, idx) => (
              <div key={m.id || idx} className="glass-card" style={{ padding: '1.1rem', background: 'rgba(10, 16, 26, 0.6)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span className="badge badge-cyan">{m.subject || 'General'}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Clock size={12} /> {m.date_display || 'Today'}
                  </span>
                </div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  {m.topic || 'Study Topic'}
                </h4>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {m.text}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
