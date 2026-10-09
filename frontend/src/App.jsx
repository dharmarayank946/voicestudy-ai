import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardView from './components/DashboardView';
import StudyView from './components/StudyView';
import MemoryView from './components/MemoryView';
import QuizView from './components/QuizView';
import ProgressView from './components/ProgressView';
import SettingsView from './components/SettingsView';
import { fetchHealth, getRecentMemories, processStudyRequest } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [healthData, setHealthData] = useState(null);
  const [memories, setMemories] = useState([]);
  const [memoryStats, setMemoryStats] = useState({ total_memories: 0, total_topics: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseData, setResponseData] = useState(null);
  const [notification, setNotification] = useState(null);

  const loadData = async () => {
    try {
      const hData = await fetchHealth();
      setHealthData(hData);
      
      const mData = await getRecentMemories(50);
      if (mData.memories) {
        setMemories(mData.memories);
        setMemoryStats({
          total_memories: mData.total_count || mData.memories.length,
          total_topics: mData.topics?.length || 3
        });
      }
    } catch (err) {
      console.warn('Failed to load initial backend data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000); // Periodic status refresh
    return () => clearInterval(interval);
  }, []);

  const showToast = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleProcessInput = async (transcript, source = 'web_speech') => {
    setIsProcessing(true);
    setResponseData(null);
    try {
      const result = await processStudyRequest(transcript, source);
      setResponseData(result);
      
      showToast(`Intent [${result.intent}] processed by ${result.agent_executed}`);

      // Refresh memory list if a new memory was saved
      if (result.intent === 'REMEMBER' || result.response_type === 'memory_saved') {
        loadData();
      }
    } catch (err) {
      showToast(`Error processing request: ${err.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleQuickSearch = (query) => {
    setActiveTab('memory');
  };

  return (
    <div className="app-container">
      {/* Toast Notification Banner */}
      {notification && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 1000,
          background: notification.type === 'error' ? 'rgba(244, 63, 94, 0.95)' : 'rgba(16, 185, 129, 0.95)',
          color: '#FFFFFF',
          padding: '0.85rem 1.25rem',
          borderRadius: '12px',
          fontWeight: '600',
          fontSize: '0.88rem',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          backdropFilter: 'blur(10px)',
          animation: 'fadeIn 0.3s ease'
        }}>
          {notification.message}
        </div>
      )}

      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        healthData={healthData} 
      />

      {/* Main App Content Area */}
      <div className="main-content">
        <Navbar 
          activeTab={activeTab} 
          onQuickSearch={handleQuickSearch} 
        />

        <main className="view-content">
          {activeTab === 'home' && (
            <DashboardView
              memories={memories}
              stats={memoryStats}
              onProcessInput={handleProcessInput}
              isProcessing={isProcessing}
              responseData={responseData}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'study' && (
            <StudyView
              onProcessInput={handleProcessInput}
              isProcessing={isProcessing}
              responseData={responseData}
            />
          )}

          {activeTab === 'memory' && (
            <MemoryView
              memories={memories}
              onRefreshMemories={loadData}
            />
          )}

          {activeTab === 'quiz' && (
            <QuizView />
          )}

          {activeTab === 'progress' && (
            <ProgressView
              memories={memories}
              stats={memoryStats}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsView
              healthData={healthData}
            />
          )}
        </main>
      </div>
    </div>
  );
}
