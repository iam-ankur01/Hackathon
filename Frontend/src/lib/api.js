import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE });

// Attach token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hs_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, clear session
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('hs_token');
      localStorage.removeItem('hs_user');
    }
    return Promise.reject(err);
  }
);

export default api;

// ── Auth ──
export const signup = (data) => api.post('/api/auth/signup', data).then(r => r.data);
export const login = (data) => api.post('/api/auth/login', data).then(r => r.data);
export const getMe = () => api.get('/api/auth/me').then(r => r.data);

export const saveSession = ({ access_token, user }) => {
  localStorage.setItem('hs_token', access_token);
  localStorage.setItem('hs_user', JSON.stringify(user));
};
export const loadSession = () => {
  const token = localStorage.getItem('hs_token');
  const user = localStorage.getItem('hs_user');
  if (!token || !user) return null;
  try { return { token, user: JSON.parse(user) }; } catch { return null; }
};
export const clearSession = () => {
  localStorage.removeItem('hs_token');
  localStorage.removeItem('hs_user');
};

// ── Profile ──
export const updateProfile = (patch) => api.patch('/api/users/me', patch).then(r => r.data);
export const uploadResume = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return api.post('/api/users/me/resume', fd).then(r => r.data);
};

// ── Interviews ──
export const submitInterview = ({ file, transcript_text, job_description, job_title, company_name }) => {
  const fd = new FormData();
  if (file) fd.append('file', file);
  if (transcript_text) fd.append('transcript_text', transcript_text);
  fd.append('job_description', job_description || '');
  fd.append('job_title', job_title || '');
  fd.append('company_name', company_name || '');
  return api.post('/api/interviews/', fd).then(r => r.data);
};
export const listInterviews = () => api.get('/api/interviews/').then(r => r.data);
export const getInterview = (id) => api.get(`/api/interviews/${id}`).then(r => r.data);

// ── Dashboard / Progress / Jobs / Coach / Roadmap ──
export const getDashboard = () => api.get('/api/dashboard').then(r => r.data);
export const getProgress = () => api.get('/api/progress').then(r => r.data);
export const getJobs = () => api.get('/api/jobs').then(r => r.data);
export const getCoach = () => api.get('/api/coach').then(r => r.data);
export const getRoadmap = (days) =>
  api.get('/api/roadmap', { params: days ? { days } : {} }).then(r => r.data);
export const saveRoadmapPreferences = (days) =>
  api.post('/api/roadmap/preferences', { days }).then(r => r.data);
export const postCoachChat = ({ message, history }) =>
  api.post('/api/coach/chat', { message, history: history || [] }).then(r => r.data);

// ── History ──
export const listHistory = () => api.get('/api/history').then(r => r.data);
export const deleteHistoryEntry = (id) => api.delete(`/api/history/${id}`).then(r => r.data);
