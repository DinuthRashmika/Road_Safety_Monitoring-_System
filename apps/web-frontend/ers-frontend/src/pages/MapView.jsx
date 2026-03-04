import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig'; 
import { GoogleMap, LoadScript, DirectionsService, DirectionsRenderer } from '@react-google-maps/api';
import './MapView.css'; 

const MapView = () => {
  const { state } = useLocation(); 
  const navigate = useNavigate(); 
  
  const [incident, setIncident] = useState(state?.incident);
  const [route, setRoute] = useState(state?.route);
  const [isUpdating, setIsUpdating] = useState(false);
  const [directionsResponse, setDirectionsResponse] = useState(null);

  // --- REPROCESSED AUTO-REFRESH FIX ---
  useEffect(() => {
    // Check if we have incident data
    if (incident && incident.id) {
      const refreshKey = `map_refresh_id_${incident.id}`;
      const hasRefreshed = sessionStorage.getItem(refreshKey);

      if (!hasRefreshed) {
        console.log("Initial map load: Triggering one-time refresh...");
        sessionStorage.setItem(refreshKey, 'true');
        
        // Use a tiny timeout to ensure storage is set before reload
        const timer = setTimeout(() => {
          window.location.reload();
        }, 100);
        
        return () => clearTimeout(timer);
      }
    }
  }, [incident]); 
  // ------------------------------------

  const mapContainerStyle = {
    width: '100%',
    height: '100%',
    borderRadius: '16px'
  };

  const mapOrigin = route?.start || (route?.path && route.path[0]) || { lat: 6.9271, lng: 79.8612 };
  const mapDestination = incident?.location || route?.end || (route?.path && route.path[1]) || { lat: 6.9271, lng: 79.8612 };

  const directionsCallback = useCallback((response) => {
    if (response !== null && response.status === 'OK') {
      setDirectionsResponse(response);
    }
  }, []);

  const handleUpdateStatus = async (newStatus) => {
    setIsUpdating(true);
    try {
      await api.post(`/api/incidents/${incident.id}/status`, { status: newStatus });
      setIncident(prev => ({ ...prev, status: newStatus }));
      if (newStatus === 'resolved') {
        navigate('/history');
      }
    } catch (err) {
      alert(`System Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const renderActionButtons = () => {
    if (!incident) return null;
    const labels = {
      'accepted': { text: 'Commence Response', class: 'btn-enroute', next: 'enroute' },
      'enroute': { text: 'Confirm Arrival', class: 'btn-arrived', next: 'arrived' },
      'arrived': { text: 'Mark Incident Resolved', class: 'btn-resolved', next: 'resolved' }
    };

    const config = labels[incident.status];
    if (!config) return <div className="resolved-banner">✓ Incident Fully Resolved</div>;

    return (
      <button 
        className={`pro-action-btn ${config.class}`} 
        onClick={() => handleUpdateStatus(config.next)} 
        disabled={isUpdating}
      >
        {isUpdating ? 'Updating...' : config.text}
      </button>
    );
  };

  if (!incident || !route) {
    return (
      <Layout>
        <div className="empty-state-container">
          <div className="empty-state-content">
            <h3>No Active Deployment</h3>
            <p>Please select an incident from your dashboard to begin navigation.</p>
            <button className="back-dash-btn" onClick={() => navigate('/')}>Return to Dashboard</button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="pro-map-wrapper">
        <aside className="pro-sidebar">
          <header className="sidebar-header-pro">
            <div className="header-top">
              <h3>Live Navigation</h3>
              <div className={`status-orb ${incident.status}`}></div>
            </div>
            <p className="incident-id-tag">Case ID: #{incident.id.toString().slice(-8)}</p>
          </header>
          
          <div className="detail-section">
            <label className="pro-label">Primary Destination</label>
            <h2 className="pro-address">{incident.location.address}</h2>
          </div>

          <div className="pro-metrics-grid">
            <div className="metric-box">
              <label className="pro-label">Est. Distance</label>
              <div className="metric-value">{route.distance_km} <span className="unit">km</span></div>
            </div>
            <div className="metric-box">
              <label className="pro-label">Current Status</label>
              <div className={`status-badge-text ${incident.status}`}>{incident.status}</div>
            </div>
          </div>

          <footer className="sidebar-footer-pro">
            {renderActionButtons()}
          </footer>
        </aside>

        <main className="map-view-area-pro">
          <LoadScript googleMapsApiKey="AIzaSyCiDuhWjlO3yK6QeYgPX-JdHtkIs78p31Q">
            <GoogleMap
              key={incident.id}
              mapContainerStyle={mapContainerStyle}
              center={mapDestination}
              zoom={14}
              options={{
                disableDefaultUI: false,
                mapTypeControl: false,
                streetViewControl: false
              }}
            >
              {!directionsResponse && (
                <DirectionsService
                  options={{ origin: mapOrigin, destination: mapDestination, travelMode: 'DRIVING' }}
                  callback={directionsCallback}
                />
              )}
              {directionsResponse && (
                <DirectionsRenderer 
                  options={{ 
                    directions: directionsResponse,
                    polylineOptions: { strokeColor: '#4f46e5', strokeWeight: 6 } 
                  }} 
                />
              )}
            </GoogleMap>
          </LoadScript>
        </main>
      </div>
    </Layout>
  );
};

export default MapView;