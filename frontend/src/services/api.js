const API_BASE_URL = 'http://localhost:8000/api';

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    console.error('Health API error:', err);
    return { status: 'offline', vector_memory: { total_memories: 0 }, voice: {} };
  }
}

export async function processStudyRequest(transcript, source = 'web_speech', subjectOverride = null, topicOverride = null) {
  const response = await fetch(`${API_BASE_URL}/study`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transcript,
      source,
      subject_override: subjectOverride,
      topic_override: topicOverride,
      device_id: source === 'omi' ? 'omi_wearable_01' : 'browser_mic'
    })
  });
  
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to process study request.');
  }
  return await response.json();
}

export async function saveMemory(text, subject = 'General', topic = 'Study Topic', memoryType = 'voice_note') {
  const response = await fetch(`${API_BASE_URL}/memory/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, subject, topic, memory_type: memoryType })
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to save memory.');
  }
  return await response.json();
}

export async function searchMemories(query, limit = 5, subjectFilter = null) {
  const response = await fetch(`${API_BASE_URL}/memory/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit, subject_filter: subjectFilter })
  });
  if (!response.ok) throw new Error('Search failed.');
  return await response.json();
}

export async function getRecentMemories(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/memory/recent?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch memories.');
  return await response.json();
}

export async function deleteMemory(memoryId) {
  const response = await fetch(`${API_BASE_URL}/memory/${memoryId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete memory.');
  return await response.json();
}

export async function generateQuiz(topic = 'Recent Studies', numQuestions = 5, difficulty = 'medium') {
  const response = await fetch(`${API_BASE_URL}/quiz`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, num_questions: numQuestions, difficulty })
  });
  if (!response.ok) throw new Error('Quiz generation failed.');
  return await response.json();
}
