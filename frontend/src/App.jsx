/**
 * App.jsx — Main application with routing.
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import InputPage from './pages/InputPage';
import ResultsPage from './pages/ResultsPage';

const App = () => {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <a href="/" className="logo">
            <span className="logo-icon">🎯</span>
            <span className="logo-text">ICD</span>
          </a>
          <nav className="nav-links">
            <a href="https://github.com/HARSH-KHEM/intelligent-candidate-discovery"
              target="_blank" rel="noopener noreferrer" className="nav-link">
              GitHub
            </a>
          </nav>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<InputPage />} />
            <Route path="/results" element={<ResultsPage />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>
            Built with ❤️ at <strong>INDIA RUNS Hackathon</strong> • Powered by
            FastAPI, FAISS & GPT-4o
          </p>
        </footer>
      </div>
    </Router>
  );
};

export default App;
