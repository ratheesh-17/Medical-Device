import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api/v1' });

export const predict = (data) => api.post('/predict', data);
export const getManufacturers = (q = '', limit = 50) => api.get('/manufacturers', { params: { q, limit } });
export const getHistory = (skip = 0, limit = 50) => api.get('/predictions', { params: { skip, limit } });
export const getMetrics = () => api.get('/metrics');
export const getHealth = () => api.get('/health');
