import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import '../assets/LoginPage.css'; 
import RoadGuruIcon from '../assets/road-guru-icon.png';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const success = await login(email, password);
    setLoading(false);
    if (!success) {
      setError('Invalid User ID or Password.');
    }
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-header">
          <img src={RoadGuruIcon} alt="Logo" className="login-logo-image" />
          <h2>Emergency Response System</h2>
          <p>Secure access for authorized personnel</p>
        </div>
        
        <div className="form-group">
          <label htmlFor="email">User ID (Email)</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your user ID"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />
        </div>
        
        {error && <p className="login-error">{error}</p>}
        
        <button type="submit" className="login-button" disabled={loading}>
          {loading ? 'Signing In...' : 'Sign In'}
        </button>
        
        <div className="login-footer">
          <p>Emergency hotline: 911 | System support: (555) 123-4567</p>
        </div>
      </form>
    </div>
  );
};

export default LoginPage;