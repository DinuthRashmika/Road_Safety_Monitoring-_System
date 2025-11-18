import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // <-- 1. IMPORT
import api from '../../api/axiosConfig';
import './IncidentModal.css';

const IncidentModal = ({ incidentId, onClose, onUpdate }) => {
  const [incident, setIncident] = useState(null);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  
  const navigate = useNavigate(); // <-- 2. INITIALIZE

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const incidentRes = await api.get(`/api/incidents/${incidentId}`);
        setIncident(incidentRes.data);
        if (incidentRes.data.status !== 'new') {
          fetchRoute(incidentId);
        }
      } catch (err) {
        setError('Failed to load incident details.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [incidentId]);

  const fetchRoute = async (id) => {
    try {
      const routeRes = await api.get(`/api/incidents/${id}/route`);
      setRoute(routeRes.data);
    } catch (err) {
      console.error('Failed to fetch route', err);
    }
  };

  const handleUpdateStatus = async (newStatus) => {
    setIsUpdating(true);
    try {
      await api.post(`/api/incidents/${incidentId}/status`, { status: newStatus });
      const incidentRes = await api.get(`/api/incidents/${incidentId}`);
      setIncident(incidentRes.data);

      if (newStatus === 'resolved') {
        alert('Incident resolved!');
        setTimeout(() => {
          onClose();
          onUpdate();
        }, 1000);
      } else {
        onUpdate();
      }
    } catch (err) {
      alert(`Failed to update status: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleAccept = async () => {
    setIsUpdating(true);
    try {
      await api.post(`/api/incidents/${incidentId}/accept`);
      const incidentRes = await api.get(`/api/incidents/${incidentId}`);
      setIncident(incidentRes.data);
      fetchRoute(incidentId);
      alert('Incident accepted. You are now assigned.');
      onUpdate();
    } catch (err) {
      alert('Failed to accept incident.');
    } finally {
      setIsUpdating(false);
    }
  };
  
  // --- 3. NEW HANDLER FUNCTION ---
  const handleGetDirections = () => {
    // Navigate to the map page and pass the incident & route data
    navigate('/map-view', { state: { incident, route } });
  };

  const renderActionButtons = () => {
    // ... (This function is unchanged)
    switch (incident.status) {
      case 'new':
        return (
          <button className="btn-accept" onClick={handleAccept} disabled={isUpdating}>
            {isUpdating ? 'Accepting...' : 'Accept Emergency & Dispatch'}
          </button>
        );
      case 'accepted':
        return (
          <button className="btn-action btn-enroute" onClick={() => handleUpdateStatus('enroute')} disabled={isUpdating}>
            {isUpdating ? '...' : 'Go Enroute'}
          </button>
        );
      case 'enroute':
        return (
          <button className="btn-action btn-arrived" onClick={() => handleUpdateStatus('arrived')} disabled={isUpdating}>
            {isUpdating ? '...' : 'Arrived at Scene'}
          </button>
        );
      case 'arrived':
        return (
          <button className="btn-action btn-resolved" onClick={() => handleUpdateStatus('resolved')} disabled={isUpdating}>
            {isUpdating ? '...' : 'Resolve Incident'}
          </button>
        );
      case 'resolved':
        return <p className="status-resolved-text">Incident Resolved</p>;
      default:
        return null;
    }
  };

  if (loading) return <div className="modal-backdrop"><div className="modal-content">Loading...</div></div>;
  if (error) return <div className="modal-backdrop"><div className="modal-content">{error} <button onClick={onClose}>Close</button></div></div>;
  if (!incident) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h3>Emergency Details - #{incident.id.split('-')[1]}</h3>
        
        <div className="modal-body">
            {/* ... (modal-left is unchanged) ... */}
            <div className="modal-left">
            <h4>Incident Information</h4>
            <p><strong>Type:</strong> {incident.source === 'traffic' ? 'Traffic Accident' : 'Violence'}</p>
            <p><strong>Score:</strong> {incident.score}</p>
            <p><strong>Reported:</strong> {new Date(incident.reported_at).toLocaleString()}</p>
            <p><strong>Location:</strong> {incident.location.address}</p>
            <h4 className="mt-2">Analysis Results</h4>
            {incident.accident?.fire_present && <p className="analysis-fire">Fire Detected</p>}
            {incident.accident && <p>Vehicles: {incident.accident.vehicles_involved}</p>}
            {incident.violence && <p>Participants: {incident.violence.participants_count}</p>}
            {incident.violence?.weapon_conf > 0 && <p>Weapon Conf: {incident.violence.weapon_conf * 100}%</p>}
            <p>Severity: {incident.severity_grade}</p>
            <h4 className="mt-2">Required Responders</h4>
            <div className="role-tags-modal">
              {incident.required_roles.map(role => (
                <span key={role} className={`role-tag ${role}`}>{role}</span>
              ))}
            </div>
          </div>
          
          {/* ... (modal-right is unchanged) ... */}
          <div className="modal-right">
            <h4>Location & Route</h4>
            {route ? (
              <div className="route-info">
                <p><strong>Fastest Route: {route.eta_min} min</strong></p>
                <p>Distance: {route.distance_km} km</p>
                <div className="map-placeholder">MAP showing route</div>
              </div>
            ) : (
              <div className="map-placeholder">Accept incident to see route.</div>
            )}
            <h4 className="mt-2">Scene Image</h4>
            <div className="scene-image-placeholder">
              {incident.media?.image_url ? 
                <img src={incident.media.image_url} alt="Scene" /> :
                'No image provided.'
              }
            </div>
          </div>
        </div>
        
        <div className="modal-footer">
          {renderActionButtons()}
          {route && incident.status !== 'resolved' && (
             // --- 4. ATTACH THE HANDLER ---
             <button className="btn-directions" onClick={handleGetDirections}>
                Get Directions
             </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IncidentModal;