import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import { useAuth } from '../hooks/useAuth';
import api from '../api/axiosConfig';
import './Profile.css'; 

const Profile = () => {
  const { id } = useParams();
  const { user: authUser } = useAuth(); 
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
        setLoading(true);
        try {
            if (id) {
                const response = await api.get(`/api/responders/${id}`);
                setUser(response.data);
            } else {
                setUser(authUser);
            }
        } catch (err) {
            console.error("Failed to load profile", err);
        } finally {
            setLoading(false);
        }
    };

    if (id || authUser) {
        fetchProfile();
    }
  }, [id, authUser]);

  if (loading) {
    return <Layout><p>Loading profile...</p></Layout>;
  }

  if (!user) {
      return <Layout><p>User profile not found.</p></Layout>;
  }

  const getInitials = (name) => {
    return name ? name.split(' ').map(n => n[0]).join('').toUpperCase() : '?';
  };

  return (
    <Layout>
      <h2>{id ? 'Responder Profile' : 'My Profile'}</h2>
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-image-placeholder">
            <span>{getInitials(user.name)}</span>
          </div>
          <div className="profile-title">
            <h3>{user.name}</h3>
            <p>{user.role.charAt(0).toUpperCase() + user.role.slice(1)}</p>
          </div>
        </div>

        <div className="profile-body">
          <div className="profile-grid">
            <div className="profile-field">
              <label>Email / User ID</label>
              <p>{user.email}</p>
            </div>
            <div className="profile-field">
              <label>Department</label>
              <p>{user.name}</p>
            </div>
            <div className="profile-field">
              <label>Station Location</label>
              <p>{user.location?.address || 'N/A'}</p>
            </div>
            <div className="profile-field">
              <label>Status</label>
              <p><span className="status-active">Active</span></p>
            </div>
            {user.contact_number && (
                <div className="profile-field">
                  <label>Contact Number</label>
                  <p>{user.contact_number}</p>
                </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Profile;