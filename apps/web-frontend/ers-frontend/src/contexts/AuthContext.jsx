import React, { createContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); 
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

 
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      fetchProfile(); 
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      
      const response = await api.get('/api/auth/me'); 
      setUser(response.data); 
    } catch (e) {
      console.error('Failed to fetch profile, logging out.', e);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/api/auth/login', { email, password });
      const { access_token } = response.data;
      
      localStorage.setItem('accessToken', access_token);
      
      await fetchProfile();

      navigate('/dashboard');
      return true;
    } catch (error) {
      console.error('Login failed', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('accessToken');
    navigate('/login');
  };

  if (loading) {
    return <div>Loading Application...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;