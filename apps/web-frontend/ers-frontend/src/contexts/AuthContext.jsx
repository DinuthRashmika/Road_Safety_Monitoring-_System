import React, { createContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // Will store the full responder object
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // On app load, check for existing token and fetch user
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      fetchProfile(); // No need to pass token
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      // ** THE FIX IS HERE **
      // Call the new /me endpoint to get our own profile
      const response = await api.get('/api/auth/me'); 
      setUser(response.data); // Store the full user object
    } catch (e) {
      console.error('Failed to fetch profile, logging out.', e);
      logout(); // Token is invalid or expired
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/api/auth/login', { email, password });
      const { access_token } = response.data;
      
      localStorage.setItem('accessToken', access_token);
      
      // After login, fetch the full user profile
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