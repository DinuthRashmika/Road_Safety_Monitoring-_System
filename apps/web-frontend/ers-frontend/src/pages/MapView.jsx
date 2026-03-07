import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import api from '../api/axiosConfig'; 
import { GoogleMap, LoadScript, MarkerF } from '@react-google-maps/api';
import './MapView.css'; 

const MapView = () => {
  const { state } = useLocation(); 
  const navigate = useNavigate(); 
  
  const [incident, setIncident] = useState(state?.incident);
  const [route, setRoute] = useState(state?.route);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (incident && incident.id) {
      const refreshKey = `map_refresh_id_${incident.id}`;
      const hasRefreshed = sessionStorage.getItem(refreshKey);

      if (!hasRefreshed) {
        sessionStorage.setItem(refreshKey, 'true');
        const timer = setTimeout(() => {
          window.location.reload();
        }, 100);
        return () => clearTimeout(timer);
      }
    }
  }, [incident]); 

  const mapContainerStyle = {
    width: '100%',
    height: '100%',
    borderRadius: '16px'
  };

  const getCoord = (obj, defaultLat, defaultLng) => {
    if (!obj || obj.lat === undefined || obj.lng === undefined) return { lat: defaultLat, lng: defaultLng };
    const lat = parseFloat(obj.lat);
    const lng = parseFloat(obj.lng);
    return {
      lat: isNaN(lat) || lat === 0 ? defaultLat : lat,
      lng: isNaN(lng) || lng === 0 ? defaultLng : lng
    };
  };

  const mapOrigin = useMemo(() => getCoord(route?.start, 6.0535, 80.2210), [route]); 
  const mapDestination = useMemo(() => getCoord(incident?.location, 6.0328, 80.2150), [incident]);

  const onLoadMap = useCallback((map) => {
    const bounds = new window.google.maps.LatLngBounds();
    bounds.extend(mapOrigin);
    bounds.extend(mapDestination);
    map.fitBounds(bounds);
  }, [mapOrigin, mapDestination]);

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

  if (!incident) {
    return (
      <Layout>
        <div className="empty-state-container">
          <div className="empty-state-content">
            <h3>No Active Deployment</h3>
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
            <p className="incident-id-tag">Case ID: #{incident.id?.toString().slice(-8)}</p>
          </header>
          
          <div className="detail-section">
            <label className="pro-label">Primary Destination</label>
            <h2 className="pro-address">{incident.location?.address || 'Location Unavailable'}</h2>
          </div>

          <div className="pro-metrics-grid">
            <div className="metric-box">
              <label className="pro-label">Est. Distance</label>
              <div className="metric-value">
                {route?.distance_km || '0'} <span className="unit">km</span>
              </div>
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
              mapContainerStyle={mapContainerStyle}
              onLoad={onLoadMap}
              options={{
                disableDefaultUI: false,
                mapTypeControl: false,
                streetViewControl: false
              }}
            >
              
              {/* Responder Base Pin (Labeled 'R') */}
              <MarkerF 
                position={mapOrigin} 
                label="R" 
                title="Responder Base" 
              />
              
              {/* Emergency Destination Pin (Labeled 'E') */}
              <MarkerF 
                position={mapDestination} 
                label="E" 
                title="Emergency Location" 
              />

            </GoogleMap>
          </LoadScript>
        </main>
      </div>
    </Layout>
  );
};

export default MapView;