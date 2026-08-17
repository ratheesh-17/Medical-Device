import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api/v1' });

// Attach JWT token to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const login = (username, password) => api.post('/auth/login', { username, password });
export const getMe = () => api.get('/auth/me');
export const getMfrAccounts = () => api.get('/auth/manufacturers');

// Prediction
export const predict = (data) => api.post('/predict', data);
export const searchDevices = (q = '', limit = 20) => api.get('/devices', { params: { q, limit } });
export const getManufacturers = (q = '', limit = 50) => api.get('/manufacturers', { params: { q, limit } });
export const getHistory = (skip = 0, limit = 50) => api.get('/predictions', { params: { skip, limit } });
export const getMetrics = () => api.get('/metrics');
export const getHealth = () => api.get('/health');

// Manufacturer dashboard
export const getMfrDashboard = () => api.get('/manufacturer/dashboard');
export const getMfrDevices = (skip = 0, limit = 50, q = '') => api.get('/manufacturer/devices', { params: { skip, limit, q } });
export const getMfrAlerts = (skip = 0, limit = 50) => api.get('/manufacturer/alerts', { params: { skip, limit } });
export const markAlertRead = (id) => api.patch(`/manufacturer/alerts/${id}/read`);
