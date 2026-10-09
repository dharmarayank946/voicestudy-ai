import React, { useState } from 'react';
import { Brain, Search, Trash2, Plus, Clock, Tag, Sparkles, Filter } from 'lucide-react';
import { saveMemory, deleteMemory, searchMemories } from '../services/api';

export default function MemoryView({ memories, onRefreshMemories }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  // New Note Form state
  const [newText, setNewText] = useState('');
  const [newSubject, setNewSubject] = useState('DBMS');
  const [newTopic, setNewTopic] = useState('Concurrency Control');

  const subjects = ['All', 'DBMS', 'Computer Networks', 'Operating Systems', 'Mathematics'];

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setIsSearching(true);
    try {
      const res = await searchMemories(searchQuery, 10, selectedSubject);
      setSearchResults(res.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newText.trim()) return;
    try {
      await saveMemory(newText, newSubject, newTopic, 'text_note');
      setNewText('');
      setShowAddModal(false);
      if (onRefreshMemories) onRefreshMemories();
    } catch (err) {
      alert(`Error saving memory: ${err.message}`);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this study memory from Qdrant?')) {
      try {
        await deleteMemory(id);
        if (searchResults) {
          setSearchResults(prev => prev ? prev.filter(m => m.id !== id) : null);
        }
        if (onRefreshMemories) onRefreshMemories();
      } catch (err) {
        alert('Failed to delete memory.');
      }
    }
  };

  const displayedMemories = searchResults || memories.filter(m => selectedSubject === 'All' || m.subject === selectedSubject);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Brain size={24} color="var(--accent-cyan)" /> Persistent Qdrant Vector Memory
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Study memories are embedded into 1536-dimensional vectors for semantic search & active recall
          </p>
        </div>

        <button className="btn-primary" onClick={() => setShowAddModal(!showAddModal)}>
          <Plus size={18} /> Add Study Note
        </button>
      </div>

      {/* Add Memory Form Modal */}
      {showAddModal && (
        <div className="glass-card" style={{ borderColor: 'var(--accent-cyan)', background: 'rgba(13, 18, 29, 0.95)' }}>
          <h4 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '1rem', color: 'var(--accent-cyan)' }}>
            + Create New Study Memory
          </h4>
          <form onSubmit={handleAddMemory} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Subject</label>
                <input
                  type="text"
                  className="custom-input"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  placeholder="e.g. DBMS"
                />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Topic</label>
                <input
                  type="text"
                  className="custom-input"
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  placeholder="e.g. Concurrency Control"
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Study Notes / Text</label>
              <textarea
                className="custom-input"
                rows={3}
                value={newText}
                onChange={(e) => setNewText(e.target.value)}
                placeholder="What did you study? Speak or write details here..."
              />
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Save to Qdrant</button>
            </div>
          </form>
        </div>
      )}

      {/* Search and Subject Filters */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        {/* Subject Filter Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {subjects.map((sub) => (
            <button
              key={sub}
              onClick={() => {
                setSelectedSubject(sub);
                setSearchResults(null);
              }}
              style={{
                padding: '0.45rem 0.9rem',
                borderRadius: '20px',
                border: selectedSubject === sub ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                background: selectedSubject === sub ? 'rgba(0, 242, 254, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                color: selectedSubject === sub ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                fontWeight: '600',
                fontSize: '0.82rem',
                cursor: 'pointer'
              }}
            >
              {sub}
            </button>
          ))}
        </div>

        {/* Semantic Search Box */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', minWidth: '320px' }}>
          <input
            type="text"
            className="custom-input"
            placeholder="Semantic vector search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '1rem', height: '38px', fontSize: '0.85rem' }}
          />
          <button type="submit" className="btn-primary" style={{ padding: '0 1rem', height: '38px' }}>
            <Search size={16} />
          </button>
        </form>
      </div>

      {/* Memories Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {displayedMemories.length === 0 ? (
          <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem 1rem' }}>
            <Brain size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem auto' }} />
            <h4 style={{ color: 'var(--text-secondary)' }}>No memories found matching your criteria</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
              Add a new study memory or clear search filters.
            </p>
          </div>
        ) : (
          displayedMemories.map((m) => (
            <div key={m.id} className="glass-card glass-card-interactive" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="badge badge-cyan">{m.subject || 'General'}</span>
                <button
                  onClick={() => handleDelete(m.id)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  title="Delete memory"
                >
                  <Trash2 size={16} color="var(--accent-rose)" />
                </button>
              </div>

              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                  {m.topic || 'Study Note'}
                </h4>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {m.text}
                </p>
              </div>

              <div style={{ marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Clock size={12} /> {m.date_display || 'Recently saved'}
                </span>
                {m.score && (
                  <span style={{ color: 'var(--accent-emerald)', fontWeight: '600' }}>
                    Match: {Math.round(m.score * 100)}%
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
