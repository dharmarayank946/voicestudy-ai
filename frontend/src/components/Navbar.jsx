import React, { useState } from 'react';
import { Search, Mic, Sparkles, Database } from 'lucide-react';

export default function Navbar({ activeTab, onQuickSearch }) {
  const [query, setQuery] = useState('');

  const titles = {
    home: 'Study Dashboard',
    study: 'Voice & Agent Interaction',
    memory: 'Qdrant Vector Memories',
    quiz: 'AI Revision Quiz',
    progress: 'Study Progress & Stats',
    settings: 'System Configuration'
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onQuickSearch) {
      onQuickSearch(query.trim());
      setQuery('');
    }
  };

  return (
    <header style={{
      padding: '1.25rem 2rem',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: 'rgba(7, 10, 15, 0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      <div>
        <h2 style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
          {titles[activeTab] || 'VoiceStudy AI'}
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Powered by Lyzr Agents • Qdrant Vector DB • Omi Voice Layer
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ position: 'relative', width: '340px' }}>
        <input
          type="text"
          className="custom-input"
          placeholder="Search study memories..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ paddingLeft: '2.5rem', height: '40px', fontSize: '0.85rem' }}
        />
        <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
      </form>
    </header>
  );
}
