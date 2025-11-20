import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Layout.css'; 
import RoadGuruIcon from '../../assets/road-guru-icon.png';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  const role = user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : '';

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-logo">
          <img src={RoadGuruIcon} alt="Logo" className="logo-image" />
          <h1>Emergency Response System</h1>
        </div>
        <div className="header-user">
          <span>{user?.name} - {role}</span>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
      </header>
      
      <div className="app-body">
        <nav className="app-sidebar">
          <div className="sidebar-sticky">
            <ul>
              <li><NavLink to="/dashboard">Dashboard</NavLink></li>
              <li><NavLink to="/map-view">Map View</NavLink></li>
              <li><NavLink to="/history">Response History</NavLink></li>
              <li><NavLink to="/profile">Profile</NavLink></li>
            </ul>
          </div>
        </nav>
        
        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;