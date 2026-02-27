import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import './Layout.css'; 

import RoadGuruIcon from '../assets/roadguru_icon.png';

const Layout = ({ children }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    return 
  };

  return (
    <div className="app-layout">
        <header className="app-header">
            <div className="header-logo">
                <img src={RoadGuruIcon} alt="Logo" className="logo-image" /> 
                <h1>Violence Detection System</h1>
            </div>
                <div className="header-user">
                <button onClick={handleLogout} className="logout-button">Logout</button>
            </div>
        </header>
      
        <div className="app-body">
            {/* <nav className="app-sidebar"> */}
                {/* <div className="sidebar-sticky"> */}
                    {/* <ul> */}
                    {/* <li><NavLink to="/dashboard">Dashboard</NavLink></li> */}
                    {/* <li><NavLink to="/history">Response History</NavLink></li> */}
                    {/* <li><NavLink to="/profile">Profile</NavLink></li> */}
                    {/* </ul> */}
            {/* </div> */}
            {/* </nav> */}
            
            <main className="app-content">
                <div className="page-container">
                    {children}
                </div>
            </main>
        </div>
    </div>
    );
};

export default Layout;