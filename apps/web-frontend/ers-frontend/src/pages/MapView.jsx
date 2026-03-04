import React, { useState, useCallback } from 'react';
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
  
  // New state to hold the calculated route line
  const [directionsResponse, setDirectionsResponse] = useState(null);

  // Map sizing
  const mapContainerStyle = {
    width: '100%',
    height: '550px',
    borderRadius: '8px'
  };

  // Safely get the Start (Responder) and End (Incident) coordinates
  const mapOrigin = route?.start || (route?.path && route.path[0]) || { lat: 6.9271, lng: 79.8612 };
  const mapDestination = incident?.location || route?.end || (route?.path && route.path[1]) || { lat: 6.9271, lng: 79.8612 };

  // This function receives the route from Google Maps and saves it to state
  const directionsCallback = useCallback((response) => {
    if (response !== null) {
      if (response.status === 'OK') {
        setDirectionsResponse(response);
      } else {
        console.log('Directions response failed: ', response);
      }
    }
  }, []);

  const handleUpdateStatus = async (newStatus) => {
    setIsUpdating(true);
    try {
      await api.post(`/api/incidents/${incident.id}/status`, { status: newStatus });
      setIncident(prev => ({ ...prev, status: newStatus }));

      if (newStatus === 'resolved') {
        alert('Incident resolved!');
        navigate('/history');
      }
    } catch (err) {
      alert(`Failed to update status: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const renderActionButtons = () => {
    if (!incident) return null;
    switch (incident.status) {
      case 'accepted': return <button className="map-action-button btn-enroute" onClick={() => handleUpdateStatus('enroute')} disabled={isUpdating}>{isUpdating ? '...' : 'Go Enroute'}</button>;
      case 'enroute': return <button className="map-action-button btn-arrived" onClick={() => handleUpdateStatus('arrived')} disabled={isUpdating}>{isUpdating ? '...' : 'Arrived at Scene'}</button>;
      case 'arrived': return <button className="map-action-button btn-resolved" onClick={() => handleUpdateStatus('resolved')} disabled={isUpdating}>{isUpdating ? '...' : 'Resolve Incident'}</button>;
      case 'resolved': return <p className="map-status-resolved">Incident Resolved</p>;
      default: return null; 
    }
  };
  
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

  return (
    <Layout>
      <h2>Map View</h2>
      <div className="map-container">
        <div className="map-info-box">
          <h4>Route: {incident.location.address}</h4>
          <p><strong>Distance:</strong> {route.distance_km} km</p>
          <p><strong>Status:</strong> <span className="status-highlight">{incident.status}</span></p>
        </div>
        
        <div className="map-actions-bar">
          {renderActionButtons()}
        </div>
        
        {/* Google Map with Directions */}
        <div style={{ marginTop: '20px' }}>
          <LoadScript googleMapsApiKey="AIzaSyCiDuhWjlO3yK6QeYgPX-JdHtkIs78p31Q">
            <GoogleMap
              mapContainerStyle={mapContainerStyle}
              center={mapDestination}
              zoom={14}
            >
              {/* 1. Request the route from Google (Only do this once!) */}
              {!directionsResponse && (
                <DirectionsService
                  options={{
                    origin: mapOrigin,
                    destination: mapDestination,
                    travelMode: 'DRIVING'
                  }}
                  callback={directionsCallback}
                />
              )}

              {/* 2. Draw the blue line and the A/B markers on the map */}
              {directionsResponse && (
                <DirectionsRenderer
                  options={{
                    directions: directionsResponse
                  }}
                />
              )}
            </GoogleMap>
          </LoadScript>
        </div>

      </div>
    </Layout>
  );
};

export default MapView;