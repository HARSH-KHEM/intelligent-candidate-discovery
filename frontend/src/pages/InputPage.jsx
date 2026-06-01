/**
 * InputPage.jsx — Main landing page for job description input and CSV upload.
 */
import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { rankCandidates, rankFromCSV } from '../services/api';

const SAMPLE_JD = `Senior Backend Engineer — 5-8 years experience

We are looking for a Senior Backend Engineer to design, build, and scale our core platform services. You will work closely with ML engineers and DevOps to ship high-impact features.

Responsibilities:
• Design and implement scalable RESTful APIs using Python (FastAPI)
• Architect distributed systems handling 50k+ requests/second
• Own database design for PostgreSQL and MongoDB
• Build CI/CD pipelines with Docker and Kubernetes
• Collaborate with ML teams to productionize models

Required: Python, FastAPI, PostgreSQL, MongoDB, Docker, Kubernetes, AWS
Preferred: GraphQL, gRPC, Kafka, TensorFlow Serving`;

const InputPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [jdText, setJdText] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [topK, setTopK] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        setError('Please upload a CSV file.');
        return;
      }
      setCsvFile(file);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!jdText.trim()) {
      setError('Please enter a job description.');
      return;
    }

    setLoading(true);
    setProgress(10);

    try {
      let result;

      if (csvFile) {
        setProgress(30);
        result = await rankFromCSV(jdText, csvFile, topK);
      } else {
        setProgress(30);
        result = await rankCandidates(jdText, null, topK);
      }

      setProgress(90);

      // Handle async job response
      if (result.status === 'pending' && result.job_id) {
        navigate('/results', {
          state: { jobId: result.job_id, isAsync: true },
        });
        return;
      }

      setProgress(100);

      // Navigate to results
      navigate('/results', {
        state: {
          results: result.ranked_candidates || result.results || [],
          totalCandidates: result.total_candidates || result.total || 0,
          processingTime: result.processing_time_ms,
          jobId: result.job_id,
        },
      });
    } catch (err) {
      console.error('Ranking failed:', err);
      setError(
        err.response?.data?.detail ||
        'Failed to rank candidates. Make sure the backend is running on port 8000.'
      );
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  const loadSampleJD = () => {
    setJdText(SAMPLE_JD);
  };

  return (
    <div className="page input-page">
      <div className="input-hero">
        <div className="hero-glow" />
        <h1 className="hero-title">
          <span className="gradient-text">Intelligent</span> Candidate Discovery
        </h1>
        <p className="hero-subtitle">
          AI-powered talent ranking that understands meaning, not just keywords.
          Upload a job description and get candidates ranked across 4 dimensions.
        </p>
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        {/* Job Description */}
        <div className="form-section">
          <div className="form-label-row">
            <label htmlFor="jd-input" className="form-label">
              Job Description
            </label>
            <button
              type="button"
              className="btn-text"
              onClick={loadSampleJD}
            >
              Load Sample JD
            </button>
          </div>
          <textarea
            id="jd-input"
            className="jd-textarea"
            placeholder="Paste your job description here..."
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            rows={12}
          />
          <span className="char-count">{jdText.length} characters</span>
        </div>

        {/* CSV Upload */}
        <div className="form-section">
          <label className="form-label">
            Candidate Profiles (CSV)
          </label>
          <div
            className={`file-dropzone ${csvFile ? 'has-file' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const file = e.dataTransfer.files[0];
              if (file) {
                setCsvFile(file);
              }
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              hidden
            />
            {csvFile ? (
              <div className="file-info">
                <span className="file-icon">📄</span>
                <span className="file-name">{csvFile.name}</span>
                <span className="file-size">
                  ({(csvFile.size / 1024).toFixed(1)} KB)
                </span>
                <button
                  type="button"
                  className="file-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    setCsvFile(null);
                  }}
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="dropzone-placeholder">
                <span className="upload-icon">⬆️</span>
                <p>Drop a CSV file here or click to browse</p>
                <p className="dropzone-hint">
                  Leave empty to use candidates from the database
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Top K */}
        <div className="form-section form-row">
          <div className="form-field">
            <label htmlFor="top-k" className="form-label">
              Top K Candidates
            </label>
            <input
              id="top-k"
              type="number"
              className="form-input"
              value={topK}
              onChange={(e) => setTopK(Math.max(1, parseInt(e.target.value) || 1))}
              min={1}
              max={500}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="error-banner">
            <span>⚠️</span> {error}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="btn-primary submit-btn"
          disabled={loading || !jdText.trim()}
        >
          {loading ? (
            <div className="loading-state">
              <div className="spinner" />
              <span>Ranking candidates... {progress > 0 ? `${progress}%` : ''}</span>
            </div>
          ) : (
            <>
              <span>🎯</span> Rank Candidates
            </>
          )}
        </button>

        {/* Progress bar */}
        {loading && (
          <div className="progress-track">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </form>

      {/* Features */}
      <div className="features-grid">
        {[
          {
            icon: '🧠',
            title: 'Semantic Matching',
            desc: 'Understands meaning, not just keywords. Finds candidates who describe skills differently.',
          },
          {
            icon: '📊',
            title: '4D Scoring',
            desc: 'Semantic match, experience fit, behavioral signals, and contextual relevance.',
          },
          {
            icon: '💡',
            title: 'AI Explanations',
            desc: 'Every candidate gets a clear, natural-language explanation of their ranking.',
          },
          {
            icon: '⚡',
            title: 'Fast & Scalable',
            desc: 'Rank 500+ candidates in seconds using FAISS vector similarity search.',
          },
        ].map((feature) => (
          <div key={feature.title} className="feature-card">
            <span className="feature-icon">{feature.icon}</span>
            <h3>{feature.title}</h3>
            <p>{feature.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InputPage;
