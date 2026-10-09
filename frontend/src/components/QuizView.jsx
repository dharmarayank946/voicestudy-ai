import React, { useState } from 'react';
import { HelpCircle, Sparkles, CheckCircle2, XCircle, RotateCcw, Award } from 'lucide-react';
import { generateQuiz } from '../services/api';

export default function QuizView() {
  const [topic, setTopic] = useState('DBMS Concurrency Control');
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState('medium');
  
  const [quizData, setQuizData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setUserAnswers({});
    setShowResults(false);
    try {
      const res = await generateQuiz(topic, numQuestions, difficulty);
      setQuizData(res);
    } catch (err) {
      alert(`Quiz generation failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const selectAnswer = (qIndex, optionIndex) => {
    if (showResults) return;
    setUserAnswers(prev => ({ ...prev, [qIndex]: optionIndex }));
  };

  const calculateScore = () => {
    if (!quizData?.questions) return 0;
    let score = 0;
    quizData.questions.forEach((q, idx) => {
      if (userAnswers[idx] === q.correct_answer) score++;
    });
    return score;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>
      {/* Quiz Controls Header */}
      <div className="glass-card">
        <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <HelpCircle size={22} color="var(--accent-purple)" /> AI Revision Quiz Generator
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Generate custom revision tests generated directly from your Qdrant study memories.
        </p>

        <form onSubmit={handleGenerate} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '0.85rem', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Revision Topic</label>
            <input
              type="text"
              className="custom-input"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. DBMS Concurrency Control"
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Questions</label>
            <select
              className="custom-input"
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
            >
              <option value={3}>3 Questions</option>
              <option value={5}>5 Questions</option>
              <option value={10}>10 Questions</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Difficulty</label>
            <select
              className="custom-input"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <button className="btn-primary" type="submit" disabled={isLoading} style={{ height: '42px' }}>
            <Sparkles size={16} /> {isLoading ? 'Generating...' : 'Generate Quiz'}
          </button>
        </form>
      </div>

      {/* Quiz Questions Container */}
      {quizData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Quiz Title Banner */}
          <div className="glass-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h4 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                {quizData.title}
              </h4>
              <span className="badge badge-purple" style={{ marginTop: '0.3rem' }}>
                Difficulty: {quizData.difficulty} • {quizData.count} Questions
              </span>
            </div>

            {showResults && (
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--accent-emerald)' }}>
                  {calculateScore()} / {quizData.questions.length}
                </span>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Score</p>
              </div>
            )}
          </div>

          {/* Question Cards */}
          {quizData.questions?.map((q, idx) => {
            const isSelected = userAnswers[idx] !== undefined;
            const isCorrect = userAnswers[idx] === q.correct_answer;

            return (
              <div key={idx} className="glass-card">
                <p style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '1rem' }}>
                  {idx + 1}. {q.question}
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {q.options?.map((opt, optIdx) => {
                    const isOptionSelected = userAnswers[idx] === optIdx;
                    const isOptionCorrect = optIdx === q.correct_answer;
                    
                    let bg = 'rgba(255, 255, 255, 0.03)';
                    let border = 'var(--border-subtle)';
                    let textColor = 'var(--text-secondary)';

                    if (showResults) {
                      if (isOptionCorrect) {
                        bg = 'rgba(16, 185, 129, 0.2)';
                        border = 'rgba(16, 185, 129, 0.6)';
                        textColor = 'var(--accent-emerald)';
                      } else if (isOptionSelected && !isOptionCorrect) {
                        bg = 'rgba(244, 63, 94, 0.2)';
                        border = 'rgba(244, 63, 94, 0.6)';
                        textColor = 'var(--accent-rose)';
                      }
                    } else if (isOptionSelected) {
                      bg = 'rgba(0, 242, 254, 0.15)';
                      border = 'var(--accent-cyan)';
                      textColor = 'var(--accent-cyan)';
                    }

                    return (
                      <button
                        key={optIdx}
                        onClick={() => selectAnswer(idx, optIdx)}
                        style={{
                          padding: '0.75rem 1rem',
                          borderRadius: '10px',
                          background: bg,
                          border: `1px solid ${border}`,
                          color: textColor,
                          fontWeight: isOptionSelected ? '600' : '400',
                          fontSize: '0.9rem',
                          textAlign: 'left',
                          cursor: showResults ? 'default' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <span>
                          <strong style={{ opacity: 0.75, marginRight: '0.5rem' }}>{String.fromCharCode(65 + optIdx)}.</strong> {opt}
                        </span>

                        {showResults && isOptionCorrect && <CheckCircle2 size={18} color="var(--accent-emerald)" />}
                        {showResults && isOptionSelected && !isOptionCorrect && <XCircle size={18} color="var(--accent-rose)" />}
                      </button>
                    );
                  })}
                </div>

                {/* Answer Explanation */}
                {showResults && (
                  <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(10, 16, 26, 0.8)', borderRadius: '10px', borderLeft: '3px solid var(--accent-cyan)', fontSize: '0.85rem' }}>
                    <strong style={{ color: 'var(--accent-cyan)' }}>Explanation: </strong>
                    <span style={{ color: 'var(--text-secondary)' }}>{q.explanation}</span>
                  </div>
                )}
              </div>
            );
          })}

          {/* Submit / Reset Actions */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem' }}>
            {!showResults ? (
              <button
                className="btn-primary"
                onClick={() => setShowResults(true)}
                disabled={Object.keys(userAnswers).length === 0}
                style={{ minWidth: '200px' }}
              >
                Submit Answers
              </button>
            ) : (
              <button
                className="btn-secondary"
                onClick={handleGenerate}
                style={{ gap: '0.5rem' }}
              >
                <RotateCcw size={16} /> Try Another Quiz
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
