import React from 'react';
import Layout from '../components/layout/Layout';
import { useAuth } from '../hooks/useAuth';
import './Profile.css'; // We will update this CSS file

// Import a placeholder image
// You can save an image in 'src/assets' and import it like this:
// import profilePlaceholder from '../assets/profile-placeholder.png';

const Profile = () => {
  const { user } = useAuth(); // Gets the logged-in user's full object
  
  if (!user) {
    return <Layout><p>Loading profile...</p></Layout>;
  }

  // A simple placeholder if you don't have a real image URL
  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  return (
    <Layout>
      <h2>Responder Profile</h2>
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-image-placeholder">
            {/* If user.imageUrl exists, use: <img src={user.imageUrl} alt="Profile" /> 
              For now, we use initials as a placeholder.
            */}
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
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Profile;