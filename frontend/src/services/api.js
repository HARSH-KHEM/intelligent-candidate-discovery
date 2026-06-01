/**
 * api.js — Axios instance pointing to the backend API.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 120000, // 2 minutes for large batch processing
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Rank candidates against a job description.
 */
export const rankCandidates = async (jdText, candidates = null, topK = 50) => {
  const payload = {
    jd_text: jdText,
    top_k: topK,
    use_reranker: true,
  };

  if (candidates) {
    payload.candidates = candidates;
  }

  const response = await api.post('/rank', payload);
  return response.data;
};

/**
 * Upload a CSV file for ranking.
 */
export const rankFromCSV = async (jdText, csvFile, topK = 50) => {
  const formData = new FormData();
  formData.append('jd_text', jdText);
  formData.append('file', csvFile);
  formData.append('top_k', topK);

  const response = await api.post('/rank/csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/**
 * Check the status of an async ranking job.
 */
export const checkJobStatus = async (jobId) => {
  const response = await api.get(`/rank/${jobId}/status`);
  return response.data;
};

/**
 * Bulk upload candidates.
 */
export const bulkUploadCandidates = async (candidates) => {
  const response = await api.post('/candidates/bulk', candidates);
  return response.data;
};

/**
 * Get candidate count.
 */
export const getCandidateCount = async () => {
  const response = await api.get('/candidates/count');
  return response.data;
};

/**
 * Health check.
 */
export const healthCheck = async () => {
  const response = await api.get('/health', { baseURL: API_BASE_URL });
  return response.data;
};

export default api;
