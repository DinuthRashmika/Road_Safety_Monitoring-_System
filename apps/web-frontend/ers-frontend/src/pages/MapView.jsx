import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig'; // Import api
import './MapView.css'; // Import the CSS

const MapView = () => {
  const { state } = useLocation(); // Get data from modal
  const navigate = useNavigate(); // To redirect after resolve
  
  // Store the incident in this page's state so we can update it
  const [incident, setIncident] = useState(state?.incident);
  const [route, setRoute] = useState(state?.route);
  const [isUpdating, setIsUpdating] = useState(false);

  // Handles all status updates
  const handleUpdateStatus = async (newStatus) => {
    setIsUpdating(true);
    try {
      await api.post(`/api/incidents/${incident.id}/status`, { status: newStatus });

      // Update the incident in our local state
      setIncident(prev => ({ ...prev, status: newStatus }));

      if (newStatus === 'resolved') {
        alert('Incident resolved!');
        // Redirect to history page
        navigate('/history');
      }
    } catch (err) {
      alert(`Failed to update status: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  // Renders the correct button based on the current status
  const renderActionButtons = () => {
    if (!incident) return null;

    switch (incident.status) {
      case 'accepted':
        return (
          <button className="map-action-button btn-enroute" onClick={() => handleUpdateStatus('enroute')} disabled={isUpdating}>
            {isUpdating ? '...' : 'Go Enroute'}
          </button>
        );
      case 'enroute':
        return (
          <button className="map-action-button btn-arrived" onClick={() => handleUpdateStatus('arrived')} disabled={isUpdating}>
            {isUpdating ? '...' : 'Arrived at Scene'}
          </button>
        );
      case 'arrived':
        return (
          <button className="map-action-button btn-resolved" onClick={() => handleUpdateStatus('resolved')} disabled={isUpdating}>
            {isUpdating ? '...' : 'Resolve Incident'}
          </button>
        );
      case 'resolved':
        return <p className="map-status-resolved">Incident Resolved</p>;
      default:
        // This includes 'new' status, which shouldn't happen here
        return null; 
    }
  };
  
  // If user lands here with no data, show a generic message
  if (!incident || !route) {
    return (
      <Layout>
        <h2>Map View</h2>
        <div className="map-container">
          <div className="map-placeholder-full">
            <h3 style={{color: '#888'}}>MAP</h3>
            <p style={{color: '#888'}}>Select an incident from the dashboard to view a route.</p>
          </div>
        </div>
      </Layout>
    );
  }

  // If we have data, show the full map page
  return (
    <Layout>
      <h2>Map View</h2>
      <div className="map-container">
        <div className="map-info-box">
          <h4>Route: {incident.location.address}</h4>
          <p><strong>Distance:</strong> {route.distance_km} km</p>
          <p><strong>Est. Time:</strong> {route.eta_min} min</p>
          <p><strong>Status:</strong> <span className="status-highlight">{incident.status}</span></p>
        </div>
        
        {/* The new action buttons are placed at the bottom */}
        <div className="map-actions-bar">
          {renderActionButtons()}
        </div>
        
        <div className="map-placeholder-full">
          <h3>MAP</h3>
          <p>(Displaying route from your station to the incident)</p>
        </div>
      </div>
    </Layout>
  );
};

export default MapView;