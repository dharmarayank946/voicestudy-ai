import React from 'react';
import { BarChart3, BookOpen, Brain, HelpCircle, Award, Calendar, CheckCircle2 } from 'lucide-react';

export default function ProgressView({ memories, stats }) {
  const subjectsCount = stats.subjects_list?.length || 3;
  const totalMemories = memories.length || stats.total_memories || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h3 style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BarChart3 size={24} color="var(--accent-emerald)" /> Study Progress & Memory Insights
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Track active recall, vector memory growth, and course subject coverage
        </p>
      </div>

      {/* Grid Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <div className="glass-card">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>Active Subjects</span>
          <h3 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.25rem' }}>{subjectsCount}</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--accent-cyan)' }}>DBMS, Computer Networks, OS</p>
        </div>

        <div className="glass-card">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>Qdrant Vectors</span>
          <h3 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.25rem' }}>{totalMemories}</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--accent-emerald)' }}>1536-dim embeddings</p>
        </div>

        <div className="glass-card">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>Revision Quizzes</span>
          <h3 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.25rem' }}>5</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--accent-purple)' }}>Average score: 85%</p>
        </div>
      </div>

      {/* Subject Coverage Breakdown */}
      <div className="glass-card">
        <h4 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1.25rem' }}>
          Subject Coverage Breakdown
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {[
            { name: 'DBMS & Database Systems', count: 4, pct: 85, color: '#00F2FE' },
            { name: 'Computer Networks & TCP/UDP', count: 3, pct: 70, color: '#10B981' },
            { name: 'Operating Systems & Paging', count: 3, pct: 60, color: '#8B5CF6' }
          ].map((item, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem' }}>
                <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{item.name}</span>
                <span style={{ color: 'var(--text-muted)' }}>{item.count} Notes ({item.pct}%)</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${item.pct}%`, height: '100%', background: item.color, borderRadius: '4px' }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
