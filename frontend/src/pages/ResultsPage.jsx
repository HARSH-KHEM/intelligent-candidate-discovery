/**
 * ResultsPage.jsx — Ranked results dashboard.
 *
 * Shows ranked candidate cards with filtering, sorting, and CSV download.
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ScoreCard from '../components/ScoreCard';
import { checkJobStatus } from '../services/api';

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [results, setResults] = useState(location.state?.results || []);
  const [totalCandidates, setTotalCandidates] = useState(location.state?.totalCandidates || 0);
  const [processingTime, setProcessingTime] = useState(location.state?.processingTime || 0);
  const [isAsync, setIsAsync] = useState(location.state?.isAsync || false);
  const [jobId] = useState(location.state?.jobId || '');

  // Filters & sorting
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState('rank');
  const [searchQuery, setSearchQuery] = useState('');

  // Async polling
  const [polling, setPolling] = useState(isAsync);
  const [pollProgress, setPollProgress] = useState(0);

  useEffect(() => {
    if (!isAsync || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const status = await checkJobStatus(jobId);
        setPollProgress(status.progress || 0);

        if (status.status === 'completed' && status.result) {
          setResults(status.result.ranked_candidates || []);
          setTotalCandidates(status.result.total_candidates || 0);
          setProcessingTime(status.result.processing_time_ms || 0);
          setPolling(false);
          setIsAsync(false);
          clearInterval(interval);
        } else if (status.status === 'failed') {
          setPolling(false);
          setIsAsync(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Polling failed:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isAsync, jobId]);

  // Filtered and sorted results
  const filteredResults = useMemo(() => {
    let filtered = results.filter((r) => (r.final_score || 0) >= minScore);

    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          (r.candidate_id || '').toLowerCase().includes(q) ||
          (r.name || '').toLowerCase().includes(q) ||
          (r.current_role || '').toLowerCase().includes(q) ||
          (r.explanation || '').toLowerCase().includes(q)
      );
    }

    // Sort
    if (sortBy === 'rank') {
      filtered.sort((a, b) => (a.rank || 0) - (b.rank || 0));
    } else if (sortBy === 'name') {
      filtered.sort((a, b) =>
        (a.name || a.candidate_id || '').localeCompare(b.name || b.candidate_id || '')
      );
    } else if (sortBy === 'score_desc') {
      filtered.sort((a, b) => (b.final_score || 0) - (a.final_score || 0));
    }

    return filtered;
  }, [results, minScore, sortBy, searchQuery]);

  // CSV download
  const downloadCSV = () => {
    const headers = [
      'candidate_id', 'rank', 'final_score', 'semantic_score',
      'experience_score', 'behavioral_score', 'context_score', 'explanation',
    ];

    const csvContent = [
      headers.join(','),
      ...filteredResults.map((r) =>
        headers.map((h) => {
          const val = r[h] ?? '';
          const str = String(val);
          return str.includes(',') || str.includes('"')
            ? `"${str.replace(/"/g, '""')}"`
            : str;
        }).join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ranked_candidates_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (polling) {
    return (
      <div className="page results-page">
        <div className="async-loading">
          <div className="spinner large" />
          <h2>Processing large batch...</h2>
          <p>Job ID: {jobId}</p>
          <div className="progress-track" style={{ maxWidth: 400, margin: '20px auto' }}>
            <div className="progress-fill" style={{ width: `${pollProgress}%` }} />
          </div>
          <p>{pollProgress.toFixed(0)}% complete</p>
        </div>
      </div>
    );
  }

  if (!results.length) {
    return (
      <div className="page results-page">
        <div className="empty-state">
          <h2>No results yet</h2>
          <p>Submit a job description to get ranked candidates.</p>
          <button className="btn-primary" onClick={() => navigate('/')}>
            ← Back to Input
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page results-page">
      {/* Header */}
      <div className="results-header">
        <div className="results-title-row">
          <button className="btn-back" onClick={() => navigate('/')}>
            ← New Search
          </button>
          <h1 className="results-title">Ranking Results</h1>
        </div>

        {/* Stats */}
        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-value">{totalCandidates}</span>
            <span className="stat-label">Total Candidates</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{filteredResults.length}</span>
            <span className="stat-label">Showing</span>
          </div>
          {processingTime > 0 && (
            <div className="stat-card">
              <span className="stat-value">
                {processingTime > 1000
                  ? `${(processingTime / 1000).toFixed(1)}s`
                  : `${processingTime.toFixed(0)}ms`}
              </span>
              <span className="stat-label">Processing Time</span>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="results-controls">
        <div className="control-group">
          <label htmlFor="search" className="control-label">Search</label>
          <input
            id="search"
            type="text"
            className="form-input"
            placeholder="Search by name, role, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="control-group">
          <label htmlFor="min-score" className="control-label">
            Min Score: {(minScore * 100).toFixed(0)}%
          </label>
          <input
            id="min-score"
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={minScore}
            onChange={(e) => setMinScore(parseFloat(e.target.value))}
            className="range-input"
          />
        </div>

        <div className="control-group">
          <label htmlFor="sort-by" className="control-label">Sort By</label>
          <select
            id="sort-by"
            className="form-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="rank">Rank</option>
            <option value="score_desc">Score (High → Low)</option>
            <option value="name">Name (A → Z)</option>
          </select>
        </div>

        <button className="btn-secondary" onClick={downloadCSV}>
          📥 Download CSV
        </button>
      </div>

      {/* Candidate Cards */}
      <div className="candidates-list">
        {filteredResults.map((candidate, i) => (
          <ScoreCard
            key={candidate.candidate_id || i}
            candidate={candidate}
            rank={candidate.rank || i + 1}
          />
        ))}
      </div>

      {filteredResults.length === 0 && (
        <div className="empty-state">
          <p>No candidates match your filters. Try lowering the minimum score.</p>
        </div>
      )}
    </div>
  );
};

export default ResultsPage;
