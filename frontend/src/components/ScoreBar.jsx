/**
 * ScoreBar.jsx — Horizontal progress bar with color coding.
 * 
 * Green (≥ 0.8), Amber (≥ 0.6), Red (< 0.6)
 */
import React from 'react';

const ScoreBar = ({ score, label, showValue = true, height = 8 }) => {
  const percentage = Math.min(100, Math.max(0, score * 100));
  
  const getColor = (val) => {
    if (val >= 0.8) return { bar: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' };
    if (val >= 0.6) return { bar: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' };
    return { bar: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' };
  };

  const colors = getColor(score);

  return (
    <div className="score-bar-container">
      {label && (
        <div className="score-bar-header">
          <span className="score-bar-label">{label}</span>
          {showValue && (
            <span className="score-bar-value" style={{ color: colors.bar }}>
              {(score * 100).toFixed(0)}%
            </span>
          )}
        </div>
      )}
      <div
        className="score-bar-track"
        style={{ height: `${height}px`, backgroundColor: colors.bg }}
      >
        <div
          className="score-bar-fill"
          style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: colors.bar,
            borderRadius: height / 2,
            transition: 'width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
          }}
        />
      </div>
    </div>
  );
};

export default ScoreBar;
