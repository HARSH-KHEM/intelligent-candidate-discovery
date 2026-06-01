/**
 * ScoreCard.jsx — Individual candidate card with radar/bar chart.
 * 
 * Shows: name, rank, final score, 4-dimension breakdown chart, AI explanation.
 */
import React, { useState } from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip,
} from 'recharts';
import ScoreBar from './ScoreBar';

const ScoreCard = ({ candidate, rank }) => {
  const [expanded, setExpanded] = useState(false);

  const {
    candidate_id,
    final_score = 0,
    semantic_score = 0,
    experience_score = 0,
    behavioral_score = 0,
    context_score = 0,
    explanation = '',
    name = candidate_id,
    current_role = '',
    location = '',
    years_experience = '',
  } = candidate;

  const radarData = [
    { dimension: 'Semantic', value: semantic_score * 100, fullMark: 100 },
    { dimension: 'Experience', value: experience_score * 100, fullMark: 100 },
    { dimension: 'Behavioral', value: behavioral_score * 100, fullMark: 100 },
    { dimension: 'Context', value: context_score * 100, fullMark: 100 },
  ];

  const getScoreClass = (score) => {
    if (score >= 0.8) return 'score-excellent';
    if (score >= 0.6) return 'score-good';
    return 'score-low';
  };

  return (
    <div className={`score-card ${expanded ? 'expanded' : ''}`}>
      {/* Header */}
      <div className="score-card-header" onClick={() => setExpanded(!expanded)}>
        <div className="score-card-rank">
          <span className="rank-badge">#{rank}</span>
        </div>

        <div className="score-card-info">
          <h3 className="candidate-name">{name || candidate_id}</h3>
          <div className="candidate-meta">
            {current_role && <span className="meta-tag">{current_role}</span>}
            {years_experience && <span className="meta-tag">{years_experience}y exp</span>}
            {location && <span className="meta-tag">{location}</span>}
          </div>
        </div>

        <div className={`score-card-score ${getScoreClass(final_score)}`}>
          <span className="score-value">{(final_score * 100).toFixed(1)}</span>
          <span className="score-unit">/ 100</span>
        </div>

        <button className="expand-btn" aria-label="Toggle details">
          <svg
            width="20" height="20" viewBox="0 0 20 20" fill="none"
            style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }}
          >
            <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="score-card-details">
          <div className="score-card-grid">
            {/* Radar Chart */}
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis
                    dataKey="dimension"
                    tick={{ fill: '#a0a0b0', fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fill: '#666', fontSize: 10 }}
                  />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="#7c5cfc"
                    fill="#7c5cfc"
                    fillOpacity={0.25}
                    strokeWidth={2}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#1e1e2e',
                      border: '1px solid #333',
                      borderRadius: 8,
                      color: '#fff',
                    }}
                    formatter={(val) => [`${val.toFixed(1)}%`, 'Score']}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Score Bars */}
            <div className="scores-breakdown">
              <ScoreBar score={semantic_score} label="Semantic Match" height={10} />
              <ScoreBar score={experience_score} label="Experience Fit" height={10} />
              <ScoreBar score={behavioral_score} label="Behavioral Signals" height={10} />
              <ScoreBar score={context_score} label="Context Fit" height={10} />
            </div>
          </div>

          {/* Explanation */}
          {explanation && (
            <div className="explanation-box">
              <div className="explanation-icon">💡</div>
              <p className="explanation-text">{explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScoreCard;
