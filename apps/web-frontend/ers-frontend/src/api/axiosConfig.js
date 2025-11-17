import axios from 'axios';

// Your backend URL
const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

// This interceptor adds the token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;