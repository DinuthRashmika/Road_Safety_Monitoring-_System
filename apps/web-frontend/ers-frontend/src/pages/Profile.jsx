import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig';
import { useAuth } from '../hooks/useAuth';
import './Profile.css'; 

const Profile = () => {
  const { user } = useAuth(); // Gets the logged-in user's full object
  
  if (!user) {
    return <Layout><p>Loading profile...</p></Layout>;
  }

  return (
    <Layout>
      <h2>Responder Profile</h2>
      <div className="profile-card">
        <div className="profile-grid">
          <div className="profile-field">
            <label>Name</label>
            <p>{user.name}</p>
          </div>
          <div className="profile-field">
            <label>Role</label>
            <p>{user.role}</p>
          </div>
          <div className="profile-field">
            <label>Email / User ID</label>
            <p>{user.email}</p>
          </div>
          <div className="profile-field">
            <label>Department</label>
            <p>{user.name}</p>
          </div>
          <div className="profile-field">
            <label>Current Location</label>
            <p>{user.location?.address || 'N/A'}</p>
          </div>
          <div className="profile-field">
            <label>Status</label>
            <p><span className="status-active">Active</span></p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Profile;